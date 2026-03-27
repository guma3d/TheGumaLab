from fastapi import APIRouter
from core.state import state
import os
import pickle
from collections import Counter
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue

router = APIRouter()

@router.get("/progress")
def get_system_progress():
    total_photos = 0
    vectorized_completed = 0
    unk_date, unk_loc, unk_person = 0, 0, 0
    
    if state.qdrant_client:
        try:
            qc = state.qdrant_client
            coll = "gumaphoto_hybrid_kr"
            vectorized_completed = qc.count(collection_name=coll).count
            total_photos = vectorized_completed
            unk_date = qc.count(collection_name=coll, count_filter=Filter(
                must=[FieldCondition(key="date", match=MatchText(text="Unknown"))]
            )).count
            unk_loc = qc.count(collection_name=coll, count_filter=Filter(
                should=[
                    FieldCondition(key="location", match=MatchText(text="Unknown")),
                    FieldCondition(key="location", match=MatchText(text="위치정보없음"))
                ]
            )).count
            unk_person = qc.count(collection_name=coll, count_filter=Filter(
                must=[FieldCondition(key="people", match=MatchValue(value="Unknown People"))]
            )).count
        except Exception as e:
            print(f"[System Stats Error] Qdrant metrics: {e}")
            
    known_faces_count = len(state.known_faces) if hasattr(state, 'known_faces') and state.known_faces else 0
        
    return {
        "total_photos": total_photos,
        "db_completed": vectorized_completed,
        "unknown_date": unk_date,
        "unknown_loc": unk_loc,
        "unknown_person": unk_person,
        "known_faces_count": known_faces_count,
        "status": "healthy"
    }

import time
_CACHED_ADVANCED_STATS = None
_CACHED_STATS_TIME = 0

@router.get("/advanced")
def get_advanced_system_stats(force_refresh: bool = False):
    global _CACHED_ADVANCED_STATS, _CACHED_STATS_TIME
    
    if not state.qdrant_client:
        return {"error": "Qdrant not loaded"}
        
    # [Cache 🚀] 10분 단위 캐시를 두어 매번 2.3만 장 풀스캔하는 현상을 방어 (명시적 새로고침 시 무시)
    current_time = time.time()
    if not force_refresh and _CACHED_ADVANCED_STATS and (current_time - _CACHED_STATS_TIME < 600):
        return _CACHED_ADVANCED_STATS
    
    try:
        qc = state.qdrant_client
        coll = "gumaphoto_hybrid_kr"
        
        all_points = []
        offset = None
        while True:
            batch, next_offset = qc.scroll(
                collection_name=coll,
                limit=10000,
                with_payload=True,
                with_vectors=False,
                offset=offset
            )
            all_points.extend(batch)
            if next_offset is None:
                break
            offset = next_offset
                
        total_photos = len(all_points)
        
        counts = {
            "dates": Counter(),
            "locations": Counter(),
            "people": Counter()
        }
        
        min_date = "9999-99"
        max_date = "0000-00"
        
        for pt in all_points:
            p = pt.payload or {}
            
            p_date = p.get("date", "Unknown Date")
            if p_date != "Unknown Date" and len(p_date) >= 7:
                ym = p_date[:7]
                if ym >= "1900-01" and ym <= "2100-12":
                    if ym < min_date: min_date = ym
                    if ym > max_date: max_date = ym
                    
            if p_date != "Unknown Date" and len(p_date) >= 4:
                # YYYY-MM 등에서 연도(YYYY)만 추출
                p_date = p_date[:4]
            counts["dates"][p_date] += 1
            
            p_loc = p.get("location", "Unknown Location")
            counts["locations"][p_loc] += 1
            
            people_list = p.get("people", [])
            if not people_list:
                counts["people"]["Unknown Person"] += 1
            else:
                for person in people_list:
                    counts["people"][person] += 1
        
        known_faces_names = set()
        kf_path = "/app/data/known_faces.pkl"
        if os.path.exists(kf_path):
            try:
                with open(kf_path, "rb") as f:
                    kf_dict = pickle.load(f)
                    known_faces_names = set(kf_dict.keys())
            except: pass
            
        def format_counter(counter_obj):
            sorted_items = sorted(counter_obj.items(), key=lambda x: x[1], reverse=True)
            res = []
            for k, v in sorted_items:
                res.append({"name": k, "count": v, "pct": round((v / total_photos * 100), 1) if total_photos > 0 else 0})
            return res
            
        _CACHED_ADVANCED_STATS = {
            "total_photos": total_photos,
            "min_date": min_date if min_date != "9999-99" else None,
            "max_date": max_date if max_date != "0000-00" else None,
            "known_faces_count": len(known_faces_names),
            "known_faces_names": list(known_faces_names),
            "dates": format_counter(counts["dates"]),
            "locations": format_counter(counts["locations"]),
            "people": format_counter(counts["people"])
        }
        _CACHED_STATS_TIME = current_time
        return _CACHED_ADVANCED_STATS
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.get("/audit_logs")
async def get_audit_logs(limit: int = 5):
    import json
    import os
    trace_file = "/app/data/audit_trace.json"
    results = []
    
    if os.path.exists(trace_file):
        try:
            with open(trace_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            before_dict = {}
            after_dict = {}
            
            for line in lines:
                try:
                    data = json.loads(line)
                    tid = data.get("trace_id")
                    if not tid: continue
                    ctype = data.get("type", "")
                    
                    if ctype == "BEFORE":
                        before_dict[tid] = data
                    elif ctype == "AFTER":
                        after_dict[tid] = data
                        
                except:
                    pass
                    
            # 역순으로 최신 완료본부터 추출
            for tid, after_data in reversed(after_dict.items()):
                if tid in before_dict:
                    results.append({
                        "trace_id": tid,
                        "before": before_dict[tid],
                        "after": after_data
                    })
                    if len(results) >= limit:
                        break
        except Exception as e:
            print("Audit log load error:", e)
            pass
            
    return results

