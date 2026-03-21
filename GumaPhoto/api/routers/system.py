from fastapi import APIRouter
from core.database import SessionLocal
from core.models import Photo

router = APIRouter()

@router.get("/progress")
def get_system_progress():
    """
    [System Monitor API]
    기존 5만장의 디스크를 스캔하며 렉을 유발하던 무식한 파일시스템 워커(live_progress_tracker.py)를 대체하는 
    초고속 ORM 단일 객체 기반 시스템 현황판 모듈.
    """
    db = SessionLocal()
    try:
        # 단순 SELECT COUNT(id) 연산이므로 5만장이든 500만장이든 ms 단위로 리턴
        total_photos = db.query(Photo).filter(Photo.status.in_(['ORGANIZED', 'VECTORIZED'])).count()
        vectorized_completed = db.query(Photo).filter(Photo.status == 'VECTORIZED').count()
        
        return {
            "total_photos": total_photos,
            "db_completed": vectorized_completed,
            "status": "healthy"
        }
    finally:
        db.close()
