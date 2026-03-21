import os
import hashlib
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
        with open(filepath, 'rb') as afile:
            buf = afile.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(65536)
        return hasher.hexdigest()

    def is_already_processed_db_only(self, filepath):
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter(Photo.filepath == filepath).first()
            if photo and photo.status == 'VECTORIZED':
                return True
            return False
        finally:
            db.close()

    def mark_done(self, filepath):
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter(Photo.filepath == filepath).first()
            if photo:
                photo.status = 'VECTORIZED'
            else:
                new_photo = Photo(filepath=filepath, file_hash=self.get_file_hash(filepath), status='VECTORIZED')
                db.add(new_photo)
            db.commit()
        finally:
            db.close()

    def mark_error(self, filepath):
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter(Photo.filepath == filepath).first()
            if photo:
                photo.status = 'ERROR'
            else:
                new_photo = Photo(filepath=filepath, file_hash=self.get_file_hash(filepath), status='ERROR')
                db.add(new_photo)
            db.commit()
        finally:
            db.close()

    def bulk_mark(self, db_records):
        """db_records format: [(filepath, status, face_count), ...]"""
        if not db_records: return
        db = SessionLocal()
        try:
            for rec in db_records:
                filepath, status, face_count = rec[0], rec[1], rec[2]
                photo = db.query(Photo).filter(Photo.filepath == filepath).first()
                if photo:
                    photo.status = 'VECTORIZED' if status == 'DONE' else 'ERROR'
                    photo.face_count = face_count
                else:
                    new_photo = Photo(
                        filepath=filepath, 
                        file_hash=self.get_file_hash(filepath), 
                        status='VECTORIZED' if status == 'DONE' else 'ERROR', 
                        face_count=face_count
                    )
                    db.add(new_photo)
            db.commit()
        finally:
            db.close()

    def clean_slate_for_reprocess(self, filepath):
        from core.database import SessionLocal
        
        base_name = os.path.splitext(filepath)[0]
        # XMP 사이드카 파일 완전 삭제
        for p in [filepath + ".xmp", base_name + ".xmp"]:
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
                
        # WEBP 썸네일 완전 삭제
        orig_ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ""
        thumb_path = f"{base_name}_{orig_ext}.webp"
        if os.path.exists(thumb_path):
            try: os.remove(thumb_path)
            except Exception: pass
            
        # SQLite 통합 상태를 ORGANIZED로 회귀시킴 (기존의 vectorized_files 레코드 파기 대체)
        # 이제 상태가 뒤로 물러났으므로 다음 VectorIndexer 사이클에서 무조건 잡힙니다!
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter(Photo.filepath == filepath).first()
            if photo:
                photo.status = 'ORGANIZED'
                db.commit()
        finally:
            db.close()
