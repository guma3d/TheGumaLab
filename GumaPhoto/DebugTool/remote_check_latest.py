import sqlite3
import datetime

db_path = "/app/data/organizer_state.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("--- Recent 14 Processed Files ---")
cur.execute("SELECT filepath, file_hash, status, processed_at FROM processed_files ORDER BY processed_at DESC LIMIT 14")
for row in cur.fetchall():
    print(f"File: {row[0].split('/')[-1]}, Status: {row[2]}, Time: {row[3]}")

print("\n--- Recent 14 Vectorized Files ---")
cur.execute("SELECT filepath, status, face_count FROM vectorized_files ORDER BY rowid DESC LIMIT 14")
for row in cur.fetchall():
    print(f"File: {row[0].split('/')[-1]}, Status: {row[1]}, Faces: {row[2]}")

conn.close()
