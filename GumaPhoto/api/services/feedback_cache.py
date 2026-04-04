import time
import json
import os

class MockRaw:
    def __init__(self, id, payload):
        self.id = id
        self.payload = payload
import threading
import concurrent.futures
from core.state import state
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue

class FeedbackCacheManager:
    def __init__(self):
        self.queue = []
        self.is_building = False
        self.lock = threading.RLock()
        self.load_from_disk()

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
                    with_payload=["location", "date", "people", "filepath", "face_bbox"],
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
            global_covered = set()
            worker_lock = threading.Lock()
            
            def process_candidate(cand):
                tid = cand["raw"].id
                issue_key = cand["issue"]
                
                with worker_lock:
                    if f"{tid}_{issue_key}" in global_covered:
                        return
                        
                fb_type = "face" if cand["issue"] in ["Person", "People"] else "scene"
                cutoff = 0.80 if fb_type == "face" else 0.83
                
                try:
                    rec_res = state.qdrant_client.query_points(
                        collection_name="gumaphoto_hybrid_kr",
                        query=tid,
                        using=fb_type,
                        limit=10000,
                        with_payload=["location", "date", "people", "filepath", "face_bbox"]
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
                        
                    if len(unresolved_ids) > 0:
                        with worker_lock:
                            # Again check if it was covered while we queried
                            if f"{tid}_{issue_key}" in global_covered:
                                return
                            for u_id in unresolved_ids:
                                global_covered.add(f"{u_id}_{issue_key}")
                            cand["match_count"] = len(unresolved_ids)
                            cand["unresolved_ids"] = unresolved_ids
                            cluster_list.append(cand)
                            
                except Exception:
                    pass

            print(f"⚡ [FeedbackCache] Launching parallel executor with 8 workers...", flush=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                executor.map(process_candidate, candidates)

            # 3. 이슈 타입별 쿼터(Quota)를 적용하여 정렬 및 추출 (Starvation 방지)
            from collections import defaultdict
            clusters_by_issue = defaultdict(list)
            for c in cluster_list:
                clusters_by_issue[c["issue"]].append(c)
                
            for issue in clusters_by_issue:
                clusters_by_issue[issue].sort(key=lambda x: x["match_count"], reverse=True)
                
            final_queue = []
            max_total = 300
            
            # People(인물) 피드백에 50% 쿼터를 무조건 할당, 나머지를 Location/Date에 균등 분배
            people_quota = max_total // 2
            other_quota = max_total - people_quota
            
            people_candidates = clusters_by_issue.get("People", [])
            final_queue.extend(people_candidates[:people_quota])
            
            rem_people_slots = max(0, people_quota - len(people_candidates))
            actual_other_quota = other_quota + rem_people_slots
            
            other_candidates = []
            for issue, cands in clusters_by_issue.items():
                if issue != "People":
                    other_candidates.extend(cands)
                    
            other_candidates.sort(key=lambda x: x["match_count"], reverse=True)
            final_queue.extend(other_candidates[:actual_other_quota])
            
            with self.lock:
                # 안전하게 덮어쓰기
                self.queue = final_queue
                self.save_to_disk()
                
            print(f"🎉 [FeedbackCache] Generated Top {len(final_queue)} clusters in {time.time()-start_t:.2f}s! (Top 1 has {final_queue[0].get('match_count')} photos)" if final_queue else "🎉 Generated 0 clusters", flush=True)
            
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


    def save_to_disk(self):
        try:
            os.makedirs('data', exist_ok=True)
            export_list = []
            for item in self.queue:
                export_list.append({
                    "id": str(item["raw"].id),
                    "payload": item["raw"].payload,
                    "issue": item["issue"],
                    "match_count": item["match_count"],
                    "unresolved_ids": list(item["unresolved_ids"])
                })
            with open('data/feedback_queue.json', 'w', encoding='utf-8') as f:
                json.dump(export_list, f, ensure_ascii=False)
            print("[FeedbackCache] 💾 Successfully saved queue to disk persistence.", flush=True)
        except Exception as e:
            print(f"❌ Failed to save disk cache: {e}")

    def load_from_disk(self):
        try:
            if os.path.exists('data/feedback_queue.json'):
                with open('data/feedback_queue.json', 'r', encoding='utf-8') as f:
                    import_list = json.load(f)
                new_queue = []
                for entry in import_list:
                    new_queue.append({
                        "raw": MockRaw(entry["id"], entry["payload"]),
                        "issue": entry["issue"],
                        "match_count": entry["match_count"],
                        "unresolved_ids": set(entry["unresolved_ids"])
                    })
                self.queue = new_queue
                print(f"[FeedbackCache] 💾 Successfully loaded {len(self.queue)} items from disk.", flush=True)
                return True
        except Exception as e:
            print(f"❌ Failed to load disk cache: {e}")
        return False

    def pop_best(self):
        res = None
        with self.lock:
            if not self.queue:
                self.build_cache_async()
                return None
                
            # 번갈아가며 다양한 피드백이 나오도록 조치 (장소만 연속으로 나오지 못하게 방지)
            target_idx = 0
            if hasattr(self, 'last_issue_type'):
                for i, item in enumerate(self.queue):
                    if item["issue"] != self.last_issue_type:
                        target_idx = i
                        break
                        
            res = self.queue.pop(target_idx)
            self.last_issue_type = res["issue"]
            
            # 추출 후 디스크 저장 업데이트
            self.save_to_disk()
            
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
            self.save_to_disk()
            print(f"♻️ [FeedbackCache] Cache synced with processed points. Updated Queue size: {len(self.queue)}", flush=True)

feedback_cache = FeedbackCacheManager()
