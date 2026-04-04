import sqlite3
import json
import os
from collections import Counter

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

cursor.execute("SELECT filepath, metadata FROM vectorized_files")

folder_counts = Counter()

for filepath, meta_str in cursor.fetchall():
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.webp':
        continue
        
    try:
        meta = json.loads(meta_str)
        if meta.get('location') == 'Unknown Location':
            norm_path = filepath.replace('\\', '/')
            folder = os.path.basename(os.path.dirname(norm_path))
            folder_counts[folder] += 1
    except Exception:
        pass

with open('d:/TheGumaLab/GumaPhoto/unknown_overall.txt', 'w', encoding='utf-8') as f:
    f.write("Top folders with Unknown Locations (excluding .webp):\n")
    for folder, count in folder_counts.most_common(20):
        f.write(f"{folder}: {count}\n")
