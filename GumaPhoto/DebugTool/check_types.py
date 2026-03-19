import sqlite3

db_path = "/app/data/organizer_state.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in c.fetchall()])
try:
    c.execute("SELECT COUNT(*) FROM processed_files")
    print("processed_files count:", c.fetchone()[0])
except Exception as e:
    print("Error processed_files:", e)
try:
    c.execute("SELECT COUNT(*) FROM vectorized_files WHERE status='DONE'")
    print("vectorized_files DONE:", c.fetchone()[0])
except Exception as e:
    print("Error vectorized_files:", e)
conn.close()
