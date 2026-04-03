import time
import threading
import random
from core.state import state
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue

class FeedbackCacheManager:
    def __init__(self):
        self.queue = []
        self.is_building = False
        self.lock = threading.RLock()

    def _build_cache_worker(self):
        print("🚀 [FeedbackCache] Starting background cluster build...")
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
            
            random.shuffle(unknowns)
            
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
                
                if issues:
                    candidates.append({"raw": raw, "issue": random.choice(issues)})
                    
            candidates = candidates[:500]
            if not candidates:
                print("✅ [FeedbackCache] No unknowns found.")
                return

            print(f"🔍 [FeedbackCache] Assessing density for {len(candidates)} candidates...")
            
            cluster_list = []
            for cand in candidates:
                tid = cand["raw"].id
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
                        
                    cluster_list.append({
                        "cand": cand,
                        "unresolved_ids": unresolved_ids,
                        "size": len(unresolved_ids)
                    })
                except Exception as e:
                    pass

            # 크기 순 정렬
            cluster_list.sort(key=lambda x: x["size"], reverse=True)
            
            # Deduplication (가장 최상위 그룹에 포함된 사진 중복 제거)
            final_queue = []
            covered_ids = set()
            
            for item in cluster_list:
                cand = item["cand"]
                uid = str(cand["raw"].id)
                
                # 앵커 자체가 이미 다른 상위 클러스터에 먹혔다면 스킵
                if uid in covered_ids:
                    continue
                    
                # 현재 클러스터에서 이미 다른 곳에 포함된 녀석들을 뺌
                unique_set = item["unresolved_ids"] - covered_ids
                
                # 순수하게 기여하는 파급력이 없거나 적으면 메리트 감소 (가장 큰거 위주로)
                if len(unique_set) > 0:
                    cand["match_count"] = len(unique_set)
                    final_queue.append(cand)
                    covered_ids.update(unique_set)
                    
                if len(final_queue) >= 150: # Top 150 확보
                    break

            with self.lock:
                self.queue = final_queue
                
            print(f"🎉 [FeedbackCache] Generated Top {len(final_queue)} unique clusters in {time.time()-start_t:.2f}s!")
            
        except Exception as e:
            print(f"❌ [FeedbackCache] Build Error: {e}")
        finally:
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
            if len(self.queue) < 15 and not self.is_building:
                self.build_cache_async()
        return res

feedback_cache = FeedbackCacheManager()
