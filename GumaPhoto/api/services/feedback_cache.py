import time
import threading
from core.state import state
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue

class FeedbackCacheManager:
    def __init__(self):
        self.queue = []
        self.is_building = False
        self.lock = threading.RLock()

    def _build_cache_worker(self):
        print("🚀 [FeedbackCache] Starting exhaustive background cluster build...", flush=True)
        start_t = time.time()
        
        try:
            unknowns = []
            next_page_offset = None
            scroll_filter = Filter(
                should=[
                    FieldCondition(key="date", match=MatchText(text="Unknown")),
                    FieldCondition(key="location", match=MatchText(text="Unknown")),
                    FieldCondition(key="location", match=MatchText(text="위치정보없음")),
                    FieldCondition(key="people", match=MatchValue(value="Unknown Person")),
                    FieldCondition(key="people", match=MatchValue(value="Unknown People"))
                ]
            )
            
            # 1. 모든 Unknown 사진 가져오기
            while True:
                batch, next_page_offset = state.qdrant_client.scroll(
                    collection_name="gumaphoto_hybrid_kr",
                    scroll_filter=scroll_filter,
                    limit=5000,
                    offset=next_page_offset,
                    with_payload=True,
                    with_vectors=False
                )
                unknowns.extend(batch)
                if next_page_offset is None or len(unknowns) >= 30000:
                    break
                    
            candidates = []
            for raw in unknowns:
                p = raw.payload or {}
                loc = p.get("location", "")
                date_val = p.get("date", "")
                people_val = p.get("people", [])
                
                issues = []
                if "Unknown" in date_val or not date_val: issues.append("Date")
                if "위치정보없음" in loc or "Unknown" in loc or not loc: issues.append("Location")
                if any(x in ["Unknown Person", "Unknown People"] for x in people_val): issues.append("People")
                
                for issue in issues:
                    candidates.append({"raw": raw, "issue": issue})
                    
            if not candidates:
                print("✅ [FeedbackCache] No unknowns found.", flush=True)
                return

            print(f"🔍 [FeedbackCache] Exhaustively assessing density for ALL {len(candidates)} candidates...", flush=True)
            
            cluster_list = []
            
            # 2. 모든 Unknown 사진을 하나씩 루프 돌면서 유사도 덩어리 크기 측정
            # 주의: 성능을 위해 클러스터 캐싱 적용 (이미 확인된 unresolved id는 스킵하여 속도 대폭 최적화)
            global_covered = set()
            
            for cand in candidates:
                tid = cand["raw"].id
                issue_key = cand["issue"]
                
                # 이미 더 큰 클러스터 추적으로 해결될 사진이면 쿼리 생략하여 속도 폭발적 향상
                if f"{tid}_{issue_key}" in global_covered:
                    continue
                    
                fb_type = "face" if cand["issue"] in ["Person", "People"] else "scene"
                cutoff = 0.80 if fb_type == "face" else 0.83
                
                try:
                    rec_res = state.qdrant_client.query_points(
                        collection_name="gumaphoto_hybrid_kr",
                        query=tid,
                        using=fb_type,
                        limit=300,
                        with_payload=True
                    ).points
                    
                    unresolved_ids = set()
                    for h in rec_res:
                        if getattr(h, "score", 0.0) < cutoff: continue
                        hp = h.payload or {}
                        
                        if fb_type != "face":
                            if "Location" in cand["issue"]:
                                loc2 = hp.get("location", "")
                                if "Unknown" not in loc2 and "위치정보없음" not in loc2 and loc2.strip() != "": continue
                            elif "Date" in cand["issue"]:
                                dt2 = hp.get("date", "")
                                if "Unknown" not in dt2 and not dt2.endswith("-Unknown"): continue
                        else:
                            p_people = hp.get("people", [])
                            if p_people and "Unknown Person" not in p_people and "Unknown People" not in p_people: continue
                                
                        unresolved_ids.add(str(h.id))
                        global_covered.add(f"{str(h.id)}_{issue_key}")
                        
                    if len(unresolved_ids) > 0:
                        cand["match_count"] = len(unresolved_ids)
                        cand["unresolved_ids"] = unresolved_ids
                        cluster_list.append(cand)
                        
                except Exception:
                    pass

            # 3. 크기 순으로 완벽하게 정렬하여 가장 큰 그룹부터 300개 선별
            cluster_list.sort(key=lambda x: x["match_count"], reverse=True)
            final_queue = cluster_list[:300]
            
            with self.lock:
                # 안전하게 덮어쓰기
                self.queue = final_queue
                
            print(f"🎉 [FeedbackCache] Generated Top {len(final_queue)} clusters in {time.time()-start_t:.2f}s!", flush=True)
            
        except Exception as e:
            print(f"❌ [FeedbackCache] Build Error: {e}", flush=True)
        finally:
            with self.lock:
                self.is_building = False

    def build_cache_async(self):
        with self.lock:
            if self.is_building:
                return
            self.is_building = True
            
        t = threading.Thread(target=self._build_cache_worker, daemon=True)
        t.start()

    def pop_best(self):
        res = None
        with self.lock:
            if not self.queue:
                self.build_cache_async()
                return None
            res = self.queue.pop(0)
            
            # 추출 후에도 큐가 너무 작으면 리필 시작
            if len(self.queue) < 15 and not self.is_building:
                self.build_cache_async()
        return res

    def remove_processed(self, processed_ids, issue_type):
        """
        4. 피드백이 처리되면 캐쉬에서 해당 사진만 제거하고 순위를 재조정
        processed_ids: 처리 완료된 점들의 ID 리스트 (문자열)
        issue_type: 'Location', 'Date', 'Person' 등 (어떤 이슈가 해결되었는지 맵핑)
        """
        if not processed_ids: return
        processed_set = set([str(x) for x in processed_ids])
        is_face_issue = "People" in issue_type or "Person" in issue_type
        
        with self.lock:
            if not self.queue: return
            
            new_queue = []
            for item in self.queue:
                item_is_face = item["issue"] in ["People", "Person"]
                # 같은 타입의 피드백(Face vs Scene)인 경우에만 해당 ID들을 해결된 것으로 간주
                if is_face_issue == item_is_face:
                    item["unresolved_ids"].difference_update(processed_set)
                    item["match_count"] = len(item["unresolved_ids"])
                
                # 아직 기여할 사진이 1장 이상 남아있는 앵커만 유지
                if item["match_count"] > 0:
                    new_queue.append(item)
                    
            # 매치 카운트가 깎였을 수 있으니 다시 정렬
            new_queue.sort(key=lambda x: x["match_count"], reverse=True)
            self.queue = new_queue
            print(f"♻️ [FeedbackCache] Cache synced with processed points. Updated Queue size: {len(self.queue)}", flush=True)

feedback_cache = FeedbackCacheManager()
