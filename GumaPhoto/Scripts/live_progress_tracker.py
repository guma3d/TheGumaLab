import sqlite3
import os
import json
import time

DB_PATH = "/app/data/organizer_state.db"
UPLOADS_DIR = "/app/data/uploads_raw"
JSON_OUTPUT = "/app/static/progress.json"

last_walk_time = 0
cached_total = 0
cached_xmp = 0

def get_progress():
    global last_walk_time, cached_total, cached_xmp
    
    # 1. 파일 검증 대기열 조회 (Queue)
    # 업로드 대기열은 파일이 적으므로 실시간(1초 단위) 체크 가능
    queue_count = 0
    if os.path.exists(UPLOADS_DIR):
        for root, dirs, files in os.walk(UPLOADS_DIR):
            queue_count += len(files)
            
    # 2. 전체 파일 수 (30초마다 갱신하여 5만장+ 스캔 시의 폭발적인 디스크 I/O 파괴 방지)
    current_time = time.time()
    if current_time - last_walk_time > 30:
        total_photos = 0
        xmp_count = 0
        if os.path.exists("/app/data/organized"):
            for root, dirs, files in os.walk("/app/data/organized"):
                for f in files:
                    f_lower = f.lower()
                    if f_lower.endswith(('.jpg', '.jpeg', '.png', '.heic')):
                        total_photos += 1
                    elif f_lower.endswith('.xmp'):
                        xmp_count += 1
        cached_total = total_photos
        cached_xmp = xmp_count
        last_walk_time = current_time
    
    db_completed = 0
    # 3. DB 작업 완료 수 (Qdrant 벡터DB에서 직접 초고속 리얼타임 조회)
    try:
        from qdrant_client import QdrantClient
        # 너무 긴 타임아웃 방지를 위해 슬림한 타임아웃 세팅
        q_client = QdrantClient("http://qdrant:6333", timeout=3)
        count_info = q_client.count(collection_name="gumaphoto_hybrid_kr", exact=True)
        db_completed = count_info.count
    except Exception as e:
        pass
        
    return {
        "queue_count": queue_count,
        "total_photos": cached_total,
        "xmp_count": cached_xmp,
        "db_completed": db_completed,
        "timestamp": current_time
    }

print("[*] Live Progress Tracker started... (with 30sec Disk I/O Throttling)")
while True:
    data = get_progress()
    try:
        with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        pass
    # 1초마다 업데이트 (디스크 탐색은 캐싱에 의해 30초마다 한 번만 디스크 긁음)
    time.sleep(1)
