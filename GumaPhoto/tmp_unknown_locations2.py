import sqlite3
import json
from collections import Counter
import os

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

cursor.execute("SELECT filepath, metadata FROM vectorized_files")

folder_counts = Counter()

for filepath, meta_str in cursor.fetchall():
    try:
        meta = json.loads(meta_str)
        if meta.get('location') == 'Unknown Location':
            # Extract folder. Windows or Linux path
            norm_path = filepath.replace('\\', '/')
            folder = os.path.basename(os.path.dirname(norm_path))
            folder_counts[folder] += 1
            
    except Exception as e:
        pass

with open('d:/TheGumaLab/GumaPhoto/unknown_locations_rank.txt', 'w', encoding='utf-8') as f:
    f.write("Top folders with most Unknown Locations:\n")
    for folder, count in folder_counts.most_common(50):
        f.write(f"{folder}: {count}\n")
