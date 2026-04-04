import sqlite3
import json
from collections import Counter

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

cursor.execute("SELECT metadata FROM vectorized_files")

people_counter = Counter()

for meta_str, in cursor.fetchall():
    try:
        meta = json.loads(meta_str)
        people = meta.get('people', [])
        for p in people:
            people_counter[p] += 1
            
    except Exception as e:
        pass

for p, count in people_counter.most_common(10):
    print(f"{p.encode('utf-8', 'replace').decode('utf-8')}: {count}")
