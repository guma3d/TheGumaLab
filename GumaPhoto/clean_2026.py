import os
import sqlite3
from qdrant_client import QdrantClient
from qdrant_client.http import models

TARGET_FILE='/app/data/organized/2026/2026-01_Hanam-Si-South-Korea/2026-01_01.jpeg'
XMP_FILE='/app/data/organized/2026/2026-01_Hanam-Si-South-Korea/2026-01_01.xmp'

for f in [TARGET_FILE, XMP_FILE]:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed: {f}")

try:
    conn = sqlite3.connect('/app/data/organizer_state.db')
    conn.execute('DELETE FROM processed_files WHERE filepath=?', (TARGET_FILE,))
    conn.execute('DELETE FROM vectorized_files WHERE filepath=?', (TARGET_FILE,))
    conn.commit()
    print("SQLite records deleted.")
except Exception as e:
    print(f"SQLite error: {e}")

try:
    client = QdrantClient(url='http://qdrant:6333')
    client.delete(
        collection_name='gumaphoto_hybrid_kr',
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(key='filepath', match=models.MatchValue(value=TARGET_FILE))
                ]
            )
        )
    )
    print("Qdrant records deleted.")
except Exception as e:
    print(f"Qdrant delete error: {e}")
