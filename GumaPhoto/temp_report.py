import uuid, os
from core.database import SessionLocal
from core.models import Photo
from qdrant_client import QdrantClient

db = SessionLocal()
photos = db.query(Photo).order_by(Photo.id.desc()).limit(2).all()
c = QdrantClient('http://qdrant:6333')

print('=== LATEST 2 PHOTOS ===\n')
for p in photos:
    print(f'---\nSQLite Filepath: {p.filepath}')
    print(f'SQLite Status: {p.status}')
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, p.filepath))
    res = c.retrieve('gumaphoto_hybrid_kr', [uid], with_payload=True)
    if res:
        print(f'Qdrant Payload: {res[0].payload}\n')
    else:
        print('Qdrant Payload: None\n')
