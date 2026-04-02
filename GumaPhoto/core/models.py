import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def get_now():
    return datetime.now(timezone.utc)

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    
    # 코어 식별자
    filepath = Column(String, unique=True, index=True, nullable=False)
    file_hash = Column(String, index=True, nullable=False)
    original_context = Column(String, default="Organized_Photo")
    
    # 궤도 추적 상태: UPLOADED -> ORGANIZED -> VECTORIZED -> DELETED (혹은 ERROR)
    status = Column(String, default="UPLOADED", index=True)
    
    # Qdrant 연결 끈 (UUID)
    qdrant_id = Column(String, default=generate_uuid, index=True, unique=True)
    
    # 프론트엔드 모바일 부드러운 스크롤을 위한 메타데이터
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # 프리미엄 부가 메타 속성
    is_favorite = Column(Boolean, default=False, index=True)
    face_count = Column(Integer, default=0)
    
    # 치명적 결함 검열 추적기
    error_trace = Column(String, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=get_now)
    updated_at = Column(DateTime, default=get_now, onupdate=get_now)

