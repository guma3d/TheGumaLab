import os
import sqlite3
import glob
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=== 1. Checking disk files ===")
search_pattern = "D:/Pictures/2019/**/*2019-12_222*"
found_files = glob.glob(search_pattern, recursive=True)
if found_files:
    for f in found_files:
        print(f"FOUND ON DISK: {f}")
else:
    print("File 2019-12_222.jpg NOT FOUND on disk.")

print("\n=== 2. Checking SQLite DB ===")
db_path = "D:/TheGumaLab/GumaPhoto/data/organizer_state.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM vectorized_files WHERE filepath LIKE '%2019-12_222%'")
    rows = cursor.fetchall()
    print(f"vectorized_files matches: {len(rows)}")
    for r in rows: print(" -", r)
except Exception as e:
    print("Error querying vectorized_files:", e)

try:
    cursor.execute("SELECT * FROM processed_files WHERE filepath LIKE '%2019-12_222%'")
    rows = cursor.fetchall()
    print(f"processed_files matches: {len(rows)}")
    for r in rows: print(" -", r)
except Exception as e:
    print("Error querying processed_files:", e)
    
conn.close()
