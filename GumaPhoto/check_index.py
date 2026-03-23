import sqlite3
import os

db_path = "/app/data/organizer_state.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("PRAGMA index_list('vectorized_files')")
indexes = c.fetchall()
print("Indexes:", indexes)
for idx in indexes:
    idx_name = idx[1]
    c.execute(f"PRAGMA index_info('{idx_name}')")
    print(f"Index {idx_name} columns:", c.fetchall())

conn.close()
