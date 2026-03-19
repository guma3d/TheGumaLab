import sqlite3

db_path = "/app/data/organizer_state.db"
import os
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # feedback_queue, sqlite_sequence, vectorized_files
    print("=== vectorized_files latest 10 ===")
    try:
        cur.execute("SELECT filepath, status FROM vectorized_files ORDER BY rowid DESC LIMIT 10;")
        for r in cur.fetchall(): print(r)
    except Exception as e: print(e)
    
    print("\n=== processed_files (if any) ===")
    try:
        cur.execute("SELECT filepath, status FROM processed_files ORDER BY rowid DESC LIMIT 10;")
        for r in cur.fetchall(): print(r)
    except Exception as e: print(e)

    conn.close()
