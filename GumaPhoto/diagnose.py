import os
import sqlite3

dir_path = "/app/data/organized"
db_path = "/app/data/organizer_state.db"

photo_count = 0
xmp_count = 0

if os.path.exists(dir_path):
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            f_lower = f.lower()
            if f_lower.endswith(('.jpg', '.jpeg', '.png', '.heic')):
                photo_count += 1
            elif f_lower.endswith('.xmp'):
                xmp_count += 1

sqlite_count = 0
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM vectorized_files WHERE status='DONE'")
    row = c.fetchone()
    if row:
        sqlite_count = row[0]
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")

print("=== 🩺 시스템 긴급 진단 결과 ===")
print(f"1. 전체 원본 사진 개수 (순수 이미지 파일): {photo_count} 장")
print(f"2. 완료된 XMP 사이드카 파일 개수: {xmp_count} 장")
print(f"3. SQLite / Qdrant 벡터 등록 완료 개수: {sqlite_count} 장")
print("================================")
