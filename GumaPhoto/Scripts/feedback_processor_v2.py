import os
import shutil
import sqlite3
import argparse
import sys
from qdrant_client import QdrantClient
import pickle

DB_PATH = "/app/data/organizer_state.db"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"
KNOWN_FACES_PATH = "/app/data/known_faces.pkl"
ORGANIZED_DIR = "/app/data/organized"

def process_time_location_feedback(qdrant_id, target_date, target_location, target_points_str="[]"):
    import json
    print(f"[*] 시간/장소 피드백 가동: 타겟 UUID {qdrant_id}, 새로운 시간: {target_date}, 새로운 장소: {target_location}")
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_str:
            target_points = json.loads(target_points_str)
    except Exception:
        pass
        
    similar_files = []
    
    # 무조건 프론트엔드에서 사용자가 명시적으로 타겟 ID 리스트를 확정하여 보낸 것만 처리
    if target_points and len(target_points) > 0:
        print(f"  [+] 사용자가 명시적으로 체크한 {len(target_points)}장의 타겟 리스트를 수신했습니다. 시뮬레이션 결과를 그대로 사용합니다.")
        points_data = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=target_points,
            with_payload=True
        )
        similar_files = [res.payload.get("filepath") for res in points_data if res.payload.get("filepath")]
    else:
        print("[-] 지정된 타겟 포인트 리스트가 없습니다. (AI 자율 스캔 전면 금지 정책에 의해 아무것도 하지 않고 종료합니다)")
        return
        
    print(f"  [+] 동일 시간/장소 집단 {len(similar_files)}장 처리 준비 완료.")
    
    import subprocess
    from geopy.geocoders import Nominatim
    
    # 3. EXIF 불변의 데이터 하드코딩
    print("  [+] EXIF Hardcoding (ExifTool / Geocoding) 구동...")
    lat, lon = None, None
    if target_location and target_location != "Unknown":
        geolocator = Nominatim(user_agent="guma_photo_organizer")
        
        # 하이픈 기준 분리 전략: [국가명] - [지역명]
        parts = target_location.split("-", 1)
        if len(parts) == 2:
            query = {"country": parts[0].strip(), "city": parts[1].strip()}
        else:
            query = {"q": target_location.replace("-", " ")}
            
        try:
            loc_data = geolocator.geocode(query, language='ko', timeout=10)
            if not loc_data and len(parts) == 2: # 2차 시도 (통검색 우회)
                query_fallback = {"q": target_location.replace("-", " ")}
                loc_data = geolocator.geocode(query_fallback, language='ko', timeout=10)
                
            if loc_data:
                lat = loc_data.latitude
                lon = loc_data.longitude
                print(f"      -> Geocoding 정확도 향상 매칭 선공: '{target_location}' -> 위도 {lat}, 경도 {lon}")
            else:
                print(f"      -> Geocoding 실패: '{target_location}' 검색 결과 없음.")
        except Exception as e:
            print(f"      -> Geocoding 오류: {e}")

    for fpath in similar_files:
        if not os.path.exists(fpath):
            continue
            
        cmd = ["exiftool"]
        has_update = False
        
        if lat is not None and lon is not None:
            lat_ref = 'N' if lat >= 0 else 'S'
            lon_ref = 'E' if lon >= 0 else 'W'
            cmd.extend([
                f"-GPSLatitude={abs(lat)}",
                f"-GPSLatitudeRef={lat_ref}",
                f"-GPSLongitude={abs(lon)}",
                f"-GPSLongitudeRef={lon_ref}"
            ])
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
            print(f"      -> ExifTool 쓰기 진행: {os.path.basename(fpath)}")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 4. 기존 데이터 100% 비우고 Clean Re-index를 위해 찌꺼기 삭제
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for fpath in similar_files:
        print(f"  [+] 파생 찌꺼기 추적 삭제 진행: {fpath}")
        cur.execute("DELETE FROM vectorized_files WHERE filepath=?", (fpath,))
        xmp_path = os.path.splitext(fpath)[0] + ".xmp"
        webp_path = os.path.splitext(fpath)[0] + "_heic.webp"
        if os.path.exists(xmp_path): os.remove(xmp_path)
        if os.path.exists(webp_path): os.remove(webp_path)
        
        # 새로운 폴더 구조로 `shutil.move` 이동 로직 적용 필요
    
    conn.commit()
    conn.close()
    
    # 5. Qdrant 데이터 일괄 파기 (Payload 삭제 등)
    # TODO: delete from Qdrant by payloads
    
    print("[*] 피드백 이동 처리가 끝나면 연계된 vector_indexer.py 가 즉시 구동되어 족보(DB)를 최신화할 것입니다.")

def process_face_enrollment(qdrant_id, known_name, target_points_str="[]"):
    import json
    print(f"[*] 인물 학습 가동: 타겟 UUID {qdrant_id}, 학습 지정 이름: {known_name}")
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_str:
            target_points = json.loads(target_points_str)
    except Exception:
        pass
        
    face_vectors = []
    
    if target_points and len(target_points) > 0:
        print(f"  [+] 사용자가 명시적으로 큐레이팅한 {len(target_points)}장의 얼굴 리스트를 바탕으로 학습을 진행합니다.")
        points_data = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=target_points,
            with_vectors=True
        )
        for res in points_data:
            if isinstance(res.vector, dict) and "v_face" in res.vector:
                face_vectors.append(res.vector.get("v_face"))
    else:
        print("[-] 지정된 타겟 포인트 리스트가 없습니다. (AI 자율 얼굴 스캔 전면 금지 정책에 의해 아무것도 하지 않고 종료합니다)")
        return
        
    # 3. 얼굴 벡터 평균화 연산 (Average) -> known_faces.pkl 온디맨드 즉각 반영
    if face_vectors:
        import numpy as np
        avg_vector = np.mean(face_vectors, axis=0) # 다방향 각도 압축
        
        if os.path.exists(KNOWN_FACES_PATH):
            with open(KNOWN_FACES_PATH, 'rb') as f:
                known_faces = pickle.load(f)
        else:
            known_faces = {}
            
        known_faces[known_name] = avg_vector.tolist()
        
        with open(KNOWN_FACES_PATH, 'wb') as f:
            pickle.dump(known_faces, f)
            
        print(f"  [+] 온디맨드 인물 학습 완료! ({known_name}님의 새 평균 벡터 사전 등록됨)")

    # 4. 기존 Qdrant 및 파편 데이터 일괄 비우기 (재스캔 대기)
    # TODO: SQLite / XMP 날리고 Clean Re-index

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", type=str, choices=["time_loc", "face"])
    parser.add_argument("--doc_id", type=str, required=True)
    parser.add_argument("--name", type=str)
    parser.add_argument("--date", type=str)
    parser.add_argument("--loc", type=str)
    parser.add_argument("--target_points", type=str, default="[]")
    args = parser.parse_args()
    
    if args.type == "time_loc":
        process_time_location_feedback(args.doc_id, args.date, args.loc, args.target_points)
    elif args.type == "face":
        process_face_enrollment(args.doc_id, args.name, args.target_points)
