import os
import sqlite3

def find_missing_file():
    # 1. Get all files on disk
    disk_files = set()
    total_photos = 0
    organized_dir = r"D:\TheGumaLab\GumaPhoto\data\organized"
    for root, dirs, files in os.walk(organized_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
                abs_path = os.path.join(root, f).replace("\\", "/")
                # convert to app path
                app_path = abs_path.replace("D:/TheGumaLab/GumaPhoto", "/app")
                disk_files.add(app_path)
                total_photos += 1

    # 2. Get all DONE files from SQLite
    db_files = set()
    conn = sqlite3.connect(r'D:\TheGumaLab\GumaPhoto\data\organizer_state.db')
    c = conn.cursor()
    c.execute("SELECT filepath FROM vectorized_files WHERE status='DONE'")
    for row in c.fetchall():
        db_files.add(row[0])

    print(f"Total on disk: {len(disk_files)}")
    print(f"Total in DB (DONE): {len(db_files)}")

    missing = disk_files - db_files
    print(f"Files on disk but missing from DB: {len(missing)}")
    for m in list(missing)[:10]:
        print("  Missing ->", m)
        

find_missing_file()
