import os
import shutil
import json
import subprocess
import pickle
import uuid
import numpy as np
from qdrant_client import QdrantClient
from geopy.geocoders import Nominatim

from core.database import SessionLocal
from core.models import Photo

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"
KNOWN_FACES_PATH = "/app/data/known_faces.pkl"

def process_time_location_feedback(qdrant_id, target_date, target_location, target_points_str="[]"):
    print(f"[*] 시간/장소 피드백 가동: 타겟 UUID {qdrant_id}, 새로운 시간: {target_date}, 새로운 장소: {target_location}")
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_str:
            target_points = json.loads(target_points_str)
    except Exception: pass
        
    similar_files = []
    if target_points and len(target_points) > 0:
        points_data = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=target_points,
            with_payload=True
        )
        similar_files = [res.payload.get("filepath") for res in points_data if getattr(res, 'payload', {}).get("filepath")]
    else:
        print("[-] 지정된 타겟 포인트 리스트가 없습니다. 종료합니다.")
        return
        
    print("  [+] EXIF Hardcoding (ExifTool / Geocoding) 구동...")
    lat, lon = None, None
    if target_location and target_location != "Unknown":
        geolocator = Nominatim(user_agent="guma_photo_organizer")
        parts = target_location.split("-", 1)
        query = {"country": parts[0].strip(), "city": parts[1].strip()} if len(parts) == 2 else {"q": target_location.replace("-", " ")}
            
        try:
            loc_data = geolocator.geocode(query, language='ko', timeout=10)
            if not loc_data and len(parts) == 2:
                loc_data = geolocator.geocode({"q": target_location.replace("-", " ")}, language='ko', timeout=10)
            if loc_data:
                lat, lon = loc_data.latitude, loc_data.longitude
        except Exception: pass

    for fpath in similar_files:
        if not os.path.exists(fpath): continue
            
        cmd = ["exiftool"]
        has_update = False
        
        if target_location and target_location != "Unknown":
            cmd.extend([f"-XMP:Location={target_location}"])
            has_update = True
        
        if lat is not None and lon is not None:
            lat_ref, lon_ref = ('N', 'E') if lat >= 0 and lon >= 0 else ('S', 'W')
            if lat < 0 and lon >= 0: lat_ref, lon_ref = 'S', 'E'
            if lat >= 0 and lon < 0: lat_ref, lon_ref = 'N', 'W'
            if lat < 0 and lon < 0: lat_ref, lon_ref = 'S', 'W'
            
            cmd.extend([f"-GPSLatitude={abs(lat)}", f"-GPSLatitudeRef={lat_ref}", f"-GPSLongitude={abs(lon)}", f"-GPSLongitudeRef={lon_ref}"])
            has_update = True
            
        if target_date and target_date != "Unknown":
            parts = target_date.split("-")
            yyyy = parts[0]
            mm = parts[1] if len(parts) > 1 else "01"
            dd = parts[2] if len(parts) > 2 else "01"
            exif_time = f"{yyyy}:{mm}:{dd} 12:00:00"
            cmd.extend([f"-DateTimeOriginal={exif_time}"])
            has_update = True
        
        if has_update:
            cmd.extend(["-overwrite_original", fpath])
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # ----------------------------------------------------
    # ORM SQLAlchemy - 기존 파일 경로의 기록을 `DELETED`로 사망 처리하고
    # 물리적 파일을 `uploads_raw`로 다시 이주시켜 완전 재구성 (Rebuild)
    # ----------------------------------------------------
    db = SessionLocal()
    try:
        uploads_dir = "/app/data/uploads_raw"
        os.makedirs(uploads_dir, exist_ok=True)
        
        for fpath in similar_files:
            # 1. ORM 상태 변경 (기존의 DELETE FROM 쿼리 대체)
            photo = db.query(Photo).filter(Photo.filepath == fpath).first()
            if photo:
                photo.status = 'DELETED'
            
            # 2. XMP 및 파생 WebP 썸네일 무결점 삭제
            base_name = os.path.splitext(fpath)[0]
            for p in [fpath + ".xmp", base_name + ".xmp", base_name + "_heic.webp", base_name + "_png.webp", base_name + "_jpg.webp"]:
                if os.path.exists(p):
                    try: os.remove(p)
                    except Exception: pass
            
            # 3. 파일을 `uploads_raw`로 이주시켜 Organizer/Indexer 사이클을 0에서부터 다시 밟게 만듦
            if os.path.exists(fpath):
                base, ext = os.path.splitext(os.path.basename(fpath))
                # _fbpass_ 토큰을 삽입하여 Organizer의 엄격한 Hash/Blur 검열을 프리패스하도록 유도!
                safe_new_name = f"{base}_fbpass_{uuid.uuid4().hex[:8]}{ext}"
                shutil.move(fpath, os.path.join(uploads_dir, safe_new_name))
        
        db.commit()
    finally:
        db.close()
    
    # Qdrant 내부의 낡은 벡터 포인트 1:N 모두 파기 (새로 생성될 것이므로)
    if target_points:
        client.delete(collection_name=COLLECTION_NAME, points_selector=target_points)


def process_face_enrollment(qdrant_id, known_name, target_points_str="[]"):
    print(f"[*] 인물 학습 가동: 타겟 UUID {qdrant_id}, 학습 지정 이름: {known_name}")
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_str:
            target_points = json.loads(target_points_str)
    except Exception: pass
        
    face_vectors = []
    if target_points and len(target_points) > 0:
        points_data = client.retrieve(collection_name=COLLECTION_NAME, ids=target_points, with_vectors=True)
        for res in points_data:
            if isinstance(res.vector, dict) and "face" in res.vector:
                face_vectors.append(res.vector.get("face"))
            elif isinstance(res.vector, dict) and "v_face" in res.vector:
                face_vectors.append(res.vector.get("v_face"))
    
    if face_vectors:
        avg_vector = np.mean(face_vectors, axis=0)
        known_faces = {}
        if os.path.exists(KNOWN_FACES_PATH):
            with open(KNOWN_FACES_PATH, 'rb') as f:
                known_faces = pickle.load(f)
        known_faces[known_name] = avg_vector.tolist()
        with open(KNOWN_FACES_PATH, 'wb') as f:
            pickle.dump(known_faces, f)
        print(f"  [+] 온디맨드 인물 학습 완료! ({known_name}님의 새 평균 벡터 등록됨)")
