from fastapi import APIRouter
from core.database import SessionLocal
from core.models import Photo
from core.state import state
import os
import pickle
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
                # Search using Text matching for "Unknown" to catch variations
                unk_date = qc.count(collection_name=coll, count_filter=Filter(
                    must=[FieldCondition(key="date", match=MatchText(text="Unknown"))]
                )).count
                
                # Location can be "Unknown" or "위치정보없음"
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
