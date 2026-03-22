from fastapi import APIRouter
from core.database import SessionLocal
from core.models import Photo
from core.state import state
import os
import pickle
from collections import Counter
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue

router = APIRouter()

@router.get("/progress")
def get_system_progress():
    db = SessionLocal()
    try:
        total_photos = db.query(Photo).filter(Photo.status.in_(['ORGANIZED', 'VECTORIZED'])).count()
        vectorized_completed = db.query(Photo).filter(Photo.status == 'VECTORIZED').count()
        
        unk_date, unk_loc, unk_person = 0, 0, 0
        
        if state.qdrant_client:
            try:
                qc = state.qdrant_client
                coll = "gumaphoto_hybrid_kr"
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
                
        known_faces_count = 0
        kf_path = "/app/data/known_faces.pkl"
        if os.path.exists(kf_path):
            try:
                with open(kf_path, "rb") as f:
                    known_faces_count = len(pickle.load(f))
            except: pass
            
        return {
            "total_photos": total_photos,
            "db_completed": vectorized_completed,
            "unknown_date": unk_date,
            "unknown_loc": unk_loc,
            "unknown_person": unk_person,
            "known_faces_count": known_faces_count,
            "status": "healthy"
        }
    finally:
        db.close()

@router.get("/advanced")
def get_advanced_system_stats():
    if not state.qdrant_client:
        return {"error": "Qdrant not loaded"}
    
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
        
        for pt in all_points:
            p = pt.payload or {}
            
            p_date = p.get("date", "Unknown Date")
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
            
        return {
            "total_photos": total_photos,
            "known_faces_count": len(known_faces_names),
            "known_faces_names": list(known_faces_names),
            "dates": format_counter(counts["dates"]),
            "locations": format_counter(counts["locations"]),
            "people": format_counter(counts["people"])
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
