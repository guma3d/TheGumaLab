import sqlite3
import os

db_path = "/app/data/organizer_state.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT filepath FROM vectorized_files WHERE status='DONE' ORDER BY rowid DESC LIMIT 1")
row = c.fetchone()

if row:
    filepath = row[0]
    print(f"✅ 방금 처리 완료된 사진: {filepath}")
    
    # Generate expected XMP path
    xmp_path = os.path.splitext(filepath)[0] + ".xmp"
    
    if os.path.exists(xmp_path):
        print(f"\n[🤖 추출된 최신 XMP(태그 및 캡션) 내용]\n{'-'*40}")
        with open(xmp_path, "r", encoding="utf-8") as f:
            print(f.read())
        print(f"{'-'*40}")
    else:
        print("❌ XMP 파일이 아직 디스크에 생성되지 않았습니다.")
else:
    print("❌ DB에 완료(DONE)된 사진이 없습니다.")
