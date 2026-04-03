import os
import re

path = r'd:\TheGumaLab\GumaPhoto\api\services\feedback_cache.py'
code = open(path, 'r', encoding='utf-8').read()

# Add import
if 'import concurrent.futures' not in code:
    code = code.replace('import threading', 'import threading\nimport concurrent.futures')

target = """            cluster_list = []
            
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
                        limit=10000,
                        with_payload=["location", "date", "people"]
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
                    pass"""

replacement = """            cluster_list = []
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
                        with_payload=["location", "date", "people"]
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
                executor.map(process_candidate, candidates)"""

if target in code:
    code = code.replace(target, replacement)
    open(path, 'w', encoding='utf-8').write(code)
    print("Successfully patched with threading logic.")
else:
    print("Could not find target block.")
