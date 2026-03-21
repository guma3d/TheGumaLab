from fastapi import APIRouter
from pydantic import BaseModel
import os
from core.state import state
from core.database import SessionLocal
from core.models import Photo

router = APIRouter()

class DeleteRequest(BaseModel):
    filepath: str
    point_id: str

@router.delete("/api/photos")
async def delete_photo(req: DeleteRequest):
    """
    [3단 연쇄 하드딜리트 파이프라인]
    1. 물리적 파일(원본+XMP+WEBP) 사살
    2. Qdrant 벡터 증발
    3. SQLAlchemy DB Tombstone 부여 (영구 제명 상태 = DELETED)
    """
    abs_path = req.filepath
    if abs_path.startswith("/videos/"):
        abs_path = abs_path.replace("/videos/", "/app/data/organized/")
    elif abs_path.startswith("/photos/"):
        abs_path = abs_path.replace("/photos/", "/app/data/organized/")
        
    print(f"🗑️ [완전 삭제 요청] 파일: {abs_path} / Point: {req.point_id}")
    
    # [1] 서버 스토리지 디스크 파일 폭파
    try:
        if os.path.exists(abs_path):
            os.remove(abs_path)
            print(f"   ✅ [1/3] 서버 원본 파일 영구 삭제 완료")
        else:
            print(f"   ⚠️ [1/3] 서버에 원본 파일이 존재하지 않아 패스함")
            
        xmp_path_1 = abs_path + ".xmp"
        xmp_path_2 = os.path.splitext(abs_path)[0] + ".xmp"
        
        for xp in [xmp_path_1, xmp_path_2]:
            if os.path.exists(xp):
                os.remove(xp)
                
        # WEBP 썸네일 완전 삭제
        orig_ext = abs_path.rsplit('.', 1)[-1].lower() if '.' in abs_path else ""
        base_name = os.path.splitext(abs_path)[0]
        thumb_path = f"{base_name}_{orig_ext}.webp"
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
            print(f"   ✅ [1/3-파생자료] WEBP 썸네일 파일 영구 삭제 완료")
            
    except Exception as e:
        print(f"   ❌ [1/3] 파일 삭제 중 오류 발생: {e}")
        
    # [2] Qdrant DB 포인트 제거
    try:
        if state.qdrant_client:
            state.qdrant_client.delete(
                collection_name="gumaphoto_hybrid_kr",
                points_selector=[req.point_id]
            )
            print(f"   ✅ [2/3] Qdrant Vector Data 파기 완료")
    except Exception as e:
        print(f"   ❌ [2/3] Qdrant DB 삭제 중 오류 발생: {e}")
        
    # [3] SQLAlchemy ORM 영구 사망(Tombstone) 각인
    db = SessionLocal()
    try:
        photo = db.query(Photo).filter(Photo.filepath == abs_path).first()
        if photo:
            photo.status = 'DELETED'
            db.commit()
            print(f"   ✅ [3/3] SQLite 영구 삭제 마킹(Tombstone) 완료")
        else:
            # 존재조차 안 했다면 일단 생성 후 즉각 사살 (혹시라도 인덱서가 주워오는 것 방지)
            new_zombie = Photo(
                filepath=abs_path,
                file_hash="ZOMBIE_DELETED",
                status='DELETED'
            )
            db.add(new_zombie)
            db.commit()
            print(f"   ✅ [3/3] 허상 파일(Zombie) 영구 차단망 설치 완료")
    except Exception as e:
        print(f"   ❌ [3/3] SQLAlchemy Tombstone 갱신 중 오류 발생: {e}")
    finally:
        db.close()
        
    return {"message": "Successfully completely deleted the photo.", "deleted_id": req.point_id}
