import os
import sqlite3

# 1. Get all files on disk
disk_files = set()
organized_dir = "/app/data/organized"
for root, dirs, files in os.walk(organized_dir):
    for f in files:
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
            abs_path = os.path.join(root, f).replace("\\", "/")
            disk_files.add(abs_path)

# 2. Get all files in Qdrant (by fetching what's DONE in db, matching live_progress DB usage)
db_files = set()
try:
    conn = sqlite3.connect('/app/data/organizer_state.db')
    c = conn.cursor()
    c.execute("SELECT filepath FROM vectorized_files WHERE status='DONE'")
    for row in c.fetchall():
        db_files.add(row[0])
except Exception as e:
    print(f"DB Error: {e}")

print(f"Total on disk: {len(disk_files)}")
print(f"Total in vector DB status: {len(db_files)}")

missing = disk_files - db_files
print(f"Pending/Missing (On Disk, NOT indexed): {len(missing)}")
for m in list(missing)[:10]:
    print("  ->", m)
