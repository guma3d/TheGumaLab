import os
import sys
import time
from PIL import Image

# 컨테이너 내 파이썬 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import SessionLocal, engine
from core.models import Base, Photo

Image.MAX_IMAGE_PIXELS = None

def run_migration():
    print("🚀 [Migration] ORM 데이터베이스 대규모 이주(Bulk Insert) 작업을 시작합니다...")
    
    # 확실히 테이블이 생성되도록 보장
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    ORGANIZED_DIR = "/app/data/organized"
    
    if not os.path.exists(ORGANIZED_DIR):
        print(f"❌ '{ORGANIZED_DIR}' 폴더가 없습니다. 마이그레이션을 종료합니다.")
        return
        
    start_t = time.time()
    
    # 중복 이주를 막기 위해 기존에 등록된 모든 파일 경로를 Set(집합)으로 불러옴 (O(1) 검색)
    existing_paths = {p[0] for p in db.query(Photo.filepath).all()}
    
    all_photos = []
    count = 0
    skipped = 0
    
    for root, _, files in os.walk(ORGANIZED_DIR):
        for f in files:
            ext = f.lower().split('.')[-1]
            if ext in ['jpg', 'jpeg', 'png', 'heic', 'mp4', 'mov', 'avi']:
                filepath = os.path.join(root, f)
                
                # 이미 이주된 사진이면 패스
                if filepath in existing_paths:
                    skipped += 1
                    continue
                    
                w, h = 0, 0
                file_bytes = os.path.getsize(filepath)
                
                # 원본 이미지를 읽으면 디코딩에 엄청난 연산이 소모되므로, 
                # 이미 구워져있는 가벼운 Webp 썸네일을 활용하여 w, h (해상도 규격)만 0.001초만에 훔쳐옵니다.
                thumb_path = filepath.rsplit('.', 1)[0] + '_' + ext + '.webp'
                try:
                    if os.path.exists(thumb_path):
                        with Image.open(thumb_path) as im:
                            w, h = im.size
                    else:
                        with Image.open(filepath) as im:
                            w, h = im.size
                except Exception:
                    pass
                
                photo = Photo(
                    filepath=filepath,
                    file_hash=f"migrated_{file_bytes}_{time.time()}", # 러프(Rough)한 이주용 임시 해시
                    width=w,
                    height=h,
                    file_size_bytes=file_bytes,
                    original_context="migration_v2",
                    status="VECTORIZED" # 기존 /organized 에 무사히 진입한 파일들은 전부 VECTORIZED 된 것으로 간주
                )
                all_photos.append(photo)
                count += 1
                
                # 1000장 단위로 묶어서(Bulk Save) 쿼리 병목현상 제거 (SQLite 오버헤드 99% 단축)
                if count % 1000 == 0:
                    db.bulk_save_objects(all_photos)
                    db.commit()
                    all_photos = []
                    print(f"  ... 📦 {count}장 DB 고속 기입 완료 (경과시간: {time.time()-start_t:.1f}초)")
                    
    # 남은 자투리 인서트
    if all_photos:
        db.bulk_save_objects(all_photos)
        db.commit()

    db.close()
    
    print(f"\n✅ [Migration 종료] 총 {count}장의 막대한 사진 정보가 새 통합 ORM 스키마 장부에 완전히 편입되었습니다! (스킵된 사진: {skipped}장 / 총 소요시간: {time.time()-start_t:.1f}초)")

if __name__ == "__main__":
    run_migration()
