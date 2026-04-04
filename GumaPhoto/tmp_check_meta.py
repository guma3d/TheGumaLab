import sqlite3
import json

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

# Get a few rows
cursor.execute("SELECT filepath, metadata FROM vectorized_files LIMIT 10")
for filepath, meta_str in cursor.fetchall():
    try:
        meta = json.loads(meta_str)
        print(filepath)
        print(meta.get('location', 'No location key'))
    except Exception as e:
        print(e)
