from fastapi import APIRouter
from pydantic import BaseModel
from api.utils.photo_purger import PhotoPurger

router = APIRouter()

class DeleteRequest(BaseModel):
    filepath: str
    point_id: str

@router.delete("/api/photos")
async def delete_photo(req: DeleteRequest):
    """
    [3단 연쇄 하드딜리트 파이프라인 호출 톨게이트]
    핵심 비즈니스 삭제 로직은 모두 PhotoPurger 인스턴스로 위임(Delegate)하여 재사용성을 극대화합니다.
    """
    print(f"🗑️ [API Router - Delete 호출됨] 파일: {req.filepath} / Point: {req.point_id}")
    
    try:
        success, message = PhotoPurger.purge_photo_data(
            abs_path=req.filepath,
            point_id=req.point_id,
            keep_original=False
        )
        if success:
            return {"message": message, "deleted_id": req.point_id}
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=message)
    except Exception as e:
        print(f"❌ [API Router] FileManager 호출 중 치명적인 에러 발생: {e}")
        return {"error": str(e)}
