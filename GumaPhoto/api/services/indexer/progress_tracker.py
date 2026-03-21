import os
import hashlib
from PIL import Image
from core.database import SessionLocal
from core.models import Photo

class ProgressTracker:
    def __init__(self):
        print("[*] ORM Progress Tracker (SQLAlchemy) Session Management 초기화 완료")
        
    def get_original_context(self, file_hash):
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter(Photo.file_hash == file_hash).first()
            return photo.original_context if photo and photo.original_context else "Organized_Photo"
        finally:
            db.close()

    def get_file_hash(self, filepath):
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as afile:
                buf = afile.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(65536)
            return hasher.hexdigest()
        except:
            return "UNKNOWN_HASH"

    def is_already_processed_db_only(self, filepath):
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter(Photo.filepath == filepath).first()
            if photo and photo.status == 'VECTORIZED':
                return True
            return False
        finally:
            db.close()

    def _ensure_photo_exists(self, db, filepath):
        """만약 Organizer 봇을 거치지 않고 수동으로 들어온 사진일 경우, 누락된 파라미터(width, height, bytes)들을 억지로라도 복구해서 완벽하게 채웁니다."""
        photo = db.query(Photo).filter(Photo.filepath == filepath).first()
        if not photo:
            w, h = 0, 0
            file_bytes = 0
            if os.path.exists(filepath):
                file_bytes = os.path.getsize(filepath)
                # 썸네일 해상도 트릭
                ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ""
                thumb_path = filepath.rsplit('.', 1)[0] + '_' + ext + '.webp'
                try:
                    if os.path.exists(thumb_path):
                        with Image.open(thumb_path) as im: w, h = im.size
                    else:
                        with Image.open(filepath) as im: w, h = im.size
                except: pass

            photo = Photo(
                filepath=filepath, 
                file_hash=self.get_file_hash(filepath), 
                width=w, 
                height=h, 
                file_size_bytes=file_bytes,
                original_context="indexer_fallback"
            )
            db.add(photo)
            db.flush() # ID를 확보하기 위해 임시 커밋
        return photo

    def mark_done(self, filepath, point_id=""):
        db = SessionLocal()
        try:
            photo = self._ensure_photo_exists(db, filepath)
            photo.status = 'VECTORIZED'
            if point_id:
                photo.qdrant_id = point_id
                photo.error_trace = None
            db.commit()
        finally:
            db.close()

    def mark_error(self, filepath, error_trace=""):
        db = SessionLocal()
        try:
            photo = self._ensure_photo_exists(db, filepath)
            photo.status = 'ERROR'
            photo.error_trace = error_trace
            db.commit()
        finally:
            db.close()

    def bulk_mark(self, db_records):
        """db_records format: [(filepath, status, point_id), ...]"""
        if not db_records: return
        db = SessionLocal()
        try:
            for filepath, status, point_id in db_records:
                photo = self._ensure_photo_exists(db, filepath)
                
                if status == 'DONE':
                    photo.status = 'VECTORIZED'
                    photo.qdrant_id = point_id
                    photo.error_trace = None
                else:
                    photo.status = 'ERROR'
                    photo.error_trace = f"AI Batch Exception: {point_id}" # point_id 튜플 자리에 에러 메세지가 넘어올 수도 있음
                    
            db.commit()
        finally:
            db.close()

    def clean_slate_for_reprocess(self, filepath):
        from core.database import SessionLocal
        
        base_name = os.path.splitext(filepath)[0]
        for p in [filepath + ".xmp", base_name + ".xmp"]:
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
                
        orig_ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ""
        thumb_path = f"{base_name}_{orig_ext}.webp"
        if os.path.exists(thumb_path):
            try: os.remove(thumb_path)
            except Exception: pass
            
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter(Photo.filepath == filepath).first()
            if photo:
                photo.status = 'ORGANIZED'
                photo.qdrant_id = None
                db.commit()
        finally:
            db.close()
