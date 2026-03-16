import sqlite3
import os
import json
import time

DB_PATH = "/app/data/organizer_state.db"
UPLOADS_DIR = "/app/data/uploads_raw"
JSON_OUTPUT = "/app/static/progress.json"

def get_progress():
    # 1. 파일 검증 대기열 조회
    remaining = 0
    if os.path.exists(UPLOADS_DIR):
        for root, dirs, files in os.walk(UPLOADS_DIR):
            remaining += len(files)
            
    processed_count = 0
    vectorized_count = 0
    
    # 2. SQLite 결과 조회
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM processed_files")
        res = c.fetchone()
        if res:
            processed_count = res[0]
            
        c.execute("SELECT COUNT(*) FROM vectorized_files WHERE status='DONE'")
        res = c.fetchone()
        if res:
            vectorized_count = res[0]
            
        conn.close()
    except Exception as e:
        pass
        
    return {
        "remaining_raw": remaining,
        "organizer_done": processed_count,
        "vectorizer_done": max(0, vectorized_count - 13), # Subtract legacy 13 images
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
