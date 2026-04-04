import sqlite3
import json
import os

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

cursor.execute("SELECT filepath, metadata FROM vectorized_files WHERE filepath LIKE '%2017-03_위치정보없음%'")

ext_counts = {}
with_loc_count = 0
unknown_loc_count = 0

for filepath, meta_str in cursor.fetchall():
    ext = os.path.splitext(filepath)[1].lower()
    ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    try:
        meta = json.loads(meta_str)
        loc = meta.get('location')
        if loc == 'Unknown Location':
            unknown_loc_count += 1
        else:
            with_loc_count += 1
    except Exception:
        pass

print("2017-03_위치정보없음 folder analysis:")
print("Extension counts:", ext_counts)
print("Files with Unknown Location:", unknown_loc_count)
print("Files WITH Location:", with_loc_count)
