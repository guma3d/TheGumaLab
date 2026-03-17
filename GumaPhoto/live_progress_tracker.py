import sqlite3
import os
import json
import time

DB_PATH = "/app/data/organizer_state.db"
UPLOADS_DIR = "/app/data/uploads_raw"
JSON_OUTPUT = "/app/static/progress.json"

def get_progress():
    # 1. 파일 검증 대기열 조회 (Queue)
    queue_count = 0
    if os.path.exists(UPLOADS_DIR):
        for root, dirs, files in os.walk(UPLOADS_DIR):
            queue_count += len(files)
            
    total_photos = 0
    db_completed = 0
    
    # 2. 전체 파일 수 (organized 내)
    if os.path.exists("/app/data/organized"):
        for root, dirs, files in os.walk("/app/data/organized"):
            total_photos += len([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))])
    
    # 3. DB 작업 완료 수 (SQLite)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM vectorized_files WHERE status='DONE'")
        res = c.fetchone()
        if res:
            db_completed = res[0]
        conn.close()
    except Exception as e:
        pass
        
    return {
        "queue_count": queue_count,
        "total_photos": total_photos,
        "db_completed": db_completed,
        "timestamp": time.time()
    }

print("Live Progress Tracker started...")
while True:
    data = get_progress()
    try:
        with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        pass
    time.sleep(1) # 1초마다 업데이트
