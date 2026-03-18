import sqlite3

db_path = "/app/data/organizer_state.db"
import os
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("\n=== processed_files (if any) ===")
    try:
        cur.execute("SELECT filepath, status FROM processed_files;")
        rows = cur.fetchall()
        print(f"Total rows in processed_files: {len(rows)}")
        for r in rows: print(r)
    except Exception as e: print(e)

    conn.close()
