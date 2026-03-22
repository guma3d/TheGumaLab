from core.database import SessionLocal
from core.models import Photo

db = SessionLocal()
results = db.query(Photo).filter(Photo.filepath.like('%fbpass%')).all()
for r in results:
    print(r.filepath)
print("----")
results2 = db.query(Photo).filter(Photo.filepath.like('%로스%')).all()
for r in results2:
    print(r.filepath)
db.close()




