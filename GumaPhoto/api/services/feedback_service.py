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
from api.utils.photo_purger import PhotoPurger

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"
KNOWN_FACES_PATH = "/app/data/known_faces.pkl"

def get_physical_metadata_str(filepath):
    try:
        if not os.path.exists(filepath): return "EXIF: File Not Found"
        res = subprocess.run(["exiftool", "-j", "-c", "%+.6f", "-DateTimeOriginal", "-Location", "-GPSLatitude", "-GPSLongitude", filepath], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            d = json.loads(res.stdout)[0]
            lat = d.get("GPSLatitude", "None")
            lon = d.get("GPSLongitude", "None")
            gps = f"({lat}, {lon})" if lat != "None" else "No GPS"
            return f"Loc: {d.get('Location', 'None')} | GPS: {gps} | Date: {d.get('DateTimeOriginal', 'None')}"
    except Exception as e: pass
    return "EXIF: Parse Error or Empty"

def process_time_location_feedback(qdrant_id, target_date, target_location, target_points_str="[]"):
    print(f"[*] 시간/장소 피드백 가동: 타겟 UUID {qdrant_id}, 새로운 시간: {target_date}, 새로운 장소: {target_location}")
    print(f"  [🔍 CELERY DBG] 받은 target_points_str 길이: {len(target_points_str)}")
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_str:
            if isinstance(target_points_str, list):
                target_points = target_points_str
            else:
                target_points = json.loads(target_points_str)
    except Exception as e:
        print(f"  [🚨 CELERY JSON ERROR] type={type(target_points_str)}, 내용={repr(target_points_str)[:200]}, 예외={e}")
    
    if qdrant_id and qdrant_id not in target_points:
        target_points.append(qdrant_id)
        
    print(f"  [🔍 CELERY DBG] 파싱된 target_points 원소 수: {len(target_points)}")
        
    valid_targets = []
    if target_points and len(target_points) > 0:
        points_data = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=target_points,
            with_payload=True
        )
        print(f"  [🔍 CELERY DBG] Qdrant에서 retrieve된 레코드 수: {len(points_data)}")
        for res in points_data:
            p = getattr(res, 'payload', {})
            fpath = p.get("filepath")
            if fpath:
                valid_targets.append({
                    "fpath": fpath, 
                    "pt_id": res.id,
                    "old_location": p.get('location'),
                    "old_date": p.get('date')
                })
                exif_str = get_physical_metadata_str(fpath)
                print(f"  [🕵️‍♂️ AUDIT-BEFORE (Time/Loc)] File: {fpath} | Loc: {p.get('location')} | Date: {p.get('date')} | People: {p.get('people')}")
                print(f"      ㄴ [메타데이터-BEFORE]: {exif_str}")
                try:
                    with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                        tf.write(json.dumps({"type": "BEFORE", "trace_id": res.id, "hash_key": os.path.basename(fpath)[:15], "filepath": fpath, "location": p.get('location'), "date": p.get('date'), "people": p.get('people'), "exif": exif_str}, ensure_ascii=False) + "\n")
                except: pass
    else:
        print("[-] 지정된 타겟 포인트 리스트가 없습니다. 종료합니다.")
        return
    # ----------------------------------------------------
    # [💥 글로벌 DB 동기화 단계] 카카오 이름 -> OSM 형태 규격화
    # ----------------------------------------------------
    if target_location:
        import re
        match = re.search(r'^\[([-\d\.]+),\s*([-\d\.]+)\]\s*(.*)$', target_location)
        if match:
            lat_val = float(match.group(1))
            lon_val = float(match.group(2))
            raw_place = str(match.group(3)).strip()
            
            try:
                import urllib.request, json
                req_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat_val}&lon={lon_val}&format=jsonv2&accept-language=ko"
                req = urllib.request.Request(req_url, headers={'User-Agent': 'GumaPhoto-FeedbackWorker/1.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        geo_data = json.loads(resp.read().decode('utf-8'))
                        addr = geo_data.get('address', {})
                        country = addr.get('country', '')
                        city = addr.get('city', '') or addr.get('town', '') or addr.get('county', '')
                        suburb = addr.get('suburb', '') or addr.get('borough', '') or addr.get('village', '')
                        
                        clean_parts = []
                        if country: clean_parts.append(country)
                        if city: clean_parts.append(city)
                        if suburb: clean_parts.append(suburb)
                        
                        if clean_parts:
                            final_osm_name = " ".join(clean_parts)
                        else:
                            final_osm_name = geo_data.get('display_name', raw_place).split(',')[0].strip()
                        
                        # 나중에 인덱서가 재스캔해도 동일하게 인식되도록 target_location 자체를 덮어쓰기!
                        target_location = f"[{lat_val}, {lon_val}] {final_osm_name}"
                        print(f"  [📍 피드백 일관성 통합] 카카오 '{raw_place}' ➡️ OSM '{final_osm_name}'")
            except Exception as e:
                print(f"  [-] OSM 역 지오코딩 실패(원본 유지): {e}")

    # ----------------------------------------------------
    # [1단계] 메타데이터 수정 (EXIF 영구 변경)
    # ----------------------------------------------------
    valid_filepaths = [item["fpath"] for item in valid_targets]
    if valid_filepaths:
        from api.utils.metadata_editor import MetadataEditor
        success_count = MetadataEditor.stamp_metadata(valid_filepaths, target_date, target_location)
        
        # 🚨 [Auto Rollback Mechanism]
        if success_count == 0 and len(valid_filepaths) > 0:
            print(f"  [🚨 ROLLBACK 작동] 물리적 파일(EXIF) 덮어쓰기에 100% 실패했습니다! 손상 방지를 위해 Qdrant DB를 수정 전으로 즉시 자동 복구(Rollback)합니다.")
            for tg in valid_targets:
                rb_payload = {}
                if target_location and "Unknown" not in target_location: 
                    rb_payload["location"] = tg.get("old_location")
                if target_date and "Unknown" not in target_date: 
                    rb_payload["date"] = tg.get("old_date")
                
                if rb_payload:
                    try:
                        client.set_payload(collection_name=COLLECTION_NAME, payload=rb_payload, points=[tg["pt_id"]])
                    except Exception as e:
                        print(f"    [-] Rollback 실패: {e}")
            print(f"  [✅ ROLLBACK 완료] 모든 DB가 안전하게 원래 상태로 롤백되었습니다. 프로세스를 강제 종료합니다.")
            return

        print(f"  [+] 총 {success_count}개의 원본 파일 메타데이터(EXIF)가 성공적으로 덮어쓰기 완료되었습니다.")
        
        # ----------------------------------------------------
        # [2단계] 초고속 DB(Qdrant) 페이로드 즉시 덮어쓰기 (새벽 지연 없음)
        # ----------------------------------------------------
        print("  [*] 무거운 AI 인덱서(VectorIndexer)를 생략하고 Qdrant에 즉시 덮어씁니다...")
        
        # Qdrant 페이로드용 장소 이름 정제 ([lat, lon] 부분 제거)
        clean_target_location = target_location
        if target_location:
            import re
            match = re.search(r'^\[([-\d\.]+),\s*([-\d\.]+)\]\s*(.*)$', target_location)
            if match:
                clean_target_location = str(match.group(3)).strip()
                
        payload_update = {}
        if target_location and "Unknown" not in target_location:
            payload_update["location"] = clean_target_location
        if target_date and "Unknown" not in target_date:
            payload_update["date"] = target_date
            
        if payload_update:
            try:
                for tg in valid_targets:
                    client.set_payload(collection_name=COLLECTION_NAME, payload=payload_update, points=[tg["pt_id"]])
            except Exception as e:
                print(f"  [!] Qdrant 즉시 업데이트 에러: {e}")
                
        # 시스템 Audit 로그 남기기
        try:
            with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                for tg in valid_targets:
                    after_pts = client.retrieve(collection_name=COLLECTION_NAME, ids=[tg["pt_id"]], with_payload=True)
                    if after_pts:
                        ap = after_pts[0].payload or {}
                        after_date = ap.get('date', target_date)
                        after_loc = ap.get('location', clean_target_location)
                    else:
                        after_date, after_loc = target_date, clean_target_location
                        
                    exif_str = get_physical_metadata_str(tg["fpath"])
                    tf.write(json.dumps({
                        "type": "AFTER", 
                        "trace_id": tg["pt_id"], 
                        "filepath": tg["fpath"], 
                        "location": after_loc, 
                        "date": after_date,
                        "people": ap.get('people') if 'ap' in locals() else None,
                        "exif": exif_str
                    }, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"      [!] 시스템 로그 갱신 중 에러 (무시): {e}")
        
        print("  [+] 메타데이터 EXIF 주입 및 DB 덮어쓰기가 초고속으로 완료되었습니다!")


def process_face_enrollment(qdrant_id, known_name, target_points_str="[]"):
    print(f"[*] 인물 물리적 재학습 가동: 메인 UUID {qdrant_id}, 학습 지정 이름: {known_name}")
    from qdrant_client import QdrantClient
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_str:
            target_points = json.loads(target_points_str)
    except Exception: pass
    
    if qdrant_id and qdrant_id not in target_points:
        target_points.append(qdrant_id)
    
    target_filepaths = []
    if target_points:
        points_data = client.retrieve(collection_name=COLLECTION_NAME, ids=target_points, with_payload=True)
        for res in points_data:
            filepath = res.payload.get("filepath")
            face_bbox = res.payload.get("face_bbox")
            if filepath and os.path.exists(filepath):
                target_filepaths.append({
                    "filepath": filepath,
                    "face_bbox": face_bbox,
                    "point_id": res.id,
                    "old_people": res.payload.get("people", [])
                })
                
    if not target_filepaths:
        print("  [!] 이동할 유효한 파일이 없습니다. 인물 학습을 중단합니다.")
        return

    lower_name = known_name.lower().strip()
    if "unidentifiable" in lower_name or "no person" in lower_name or "no people" in lower_name:
        true_name = "No People" if "no" in lower_name else "Unidentifiable Person"
        print(f"  [*] 특별 케이스: '{true_name}' 로 바로 처리 (인물 딥러닝 스킵)")
        for target in target_filepaths:
            point_id = target["point_id"]
            filepath = target["filepath"]
            
            client.delete_payload(collection_name=COLLECTION_NAME, keys=["face_bbox"], points=[point_id])
            client.set_payload(collection_name=COLLECTION_NAME, payload={"people": [true_name]}, points=[point_id])
            
            try:
                import json
                with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                    tf.write(json.dumps({"type": "BEFORE", "trace_id": point_id, "filepath": filepath, "people": target.get("old_people", [])}, ensure_ascii=False) + "\n")
                    tf.write(json.dumps({"type": "AFTER", "trace_id": point_id, "filepath": filepath, "people": [true_name]}, ensure_ascii=False) + "\n")
            except: pass
            print(f"    - {os.path.basename(filepath)} : 업데이트 완료 [{true_name}]")
        return
        
    enrolled_dir = os.path.join("/app/data/enrolled", known_name)
    os.makedirs(enrolled_dir, exist_ok=True)
    
    import cv2
    import glob
    
    # 1. 오직 유저에게 보여준 메인 사진 1개만 크롭하여 enrolled에 포함
    main_target = next((item for item in target_filepaths if item["point_id"] == qdrant_id), target_filepaths[0])
    main_filepath = main_target['filepath']
    face_bbox = main_target['face_bbox']
    
    # 롤백 방어: 기존에 다른 위치에 저장된 조각 삭제
    old_ghosts = glob.glob(f"/app/data/enrolled/*/{qdrant_id}.jpg")
    for ghost in old_ghosts:
        try: os.remove(ghost)
        except: pass
        
    enrolled_dest = os.path.join(enrolled_dir, f"{qdrant_id}.jpg")
    if not os.path.exists(enrolled_dest):
        if face_bbox and len(face_bbox) == 4:
            try:
                img = cv2.imread(main_filepath)
                if img is not None:
                    x1, y1, x2, y2 = map(int, face_bbox)
                    h, w = img.shape[:2]
                    margin_x = int((x2 - x1) * 1.0)
                    margin_y = int((y2 - y1) * 1.0)
                    nx1, ny1 = max(0, x1 - margin_x), max(0, y1 - margin_y)
                    nx2, ny2 = min(w, x2 + margin_x), min(h, y2 + margin_y)
                    face_chip = img[ny1:ny2, nx1:nx2]
                    cv2.imwrite(enrolled_dest, face_chip)
                    print(f"  [+] 정밀 크롭(Crop) 데이터셋 축적 완료 (학습은 새벽 배치로 지연): {enrolled_dest}")
            except Exception as e:
                print(f"  [!] 얼굴 크롭 실패: {e}")
                shutil.copy2(main_filepath, enrolled_dest)
        else:
            shutil.copy2(main_filepath, enrolled_dest)

    # 2. 빠른 DB 즉시 덮어쓰기 (새벽 딥러닝 전까지 프론트엔드용으로 임시 유지)
    print("  [*] 인물 등록 딥러닝 우회 (새벽 지연). DB에 즉시 강제 덮어쓰기 중...")
    for target in target_filepaths:
        point_id = target["point_id"]
        filepath = target["filepath"]
        
        # 기존 people 리스트에서 Unnamed 등 교체 후 추가, 혹은 심플하게 덮어쓰기
        client.set_payload(collection_name=COLLECTION_NAME, payload={"people": [known_name]}, points=[point_id])
        
        try:
            import json
            with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                tf.write(json.dumps({"type": "BEFORE", "trace_id": point_id, "filepath": filepath, "people": target.get("old_people", [])}, ensure_ascii=False) + "\n")
                tf.write(json.dumps({"type": "AFTER", "trace_id": point_id, "filepath": filepath, "people": [known_name]}, ensure_ascii=False) + "\n")
        except: pass
        
        print(f"    - {os.path.basename(filepath)} : 영구 업데이트 완료 [{known_name}]")
        
    print("  [+] 인물 사진 도감 축적 및 DB 반영 모두 완료되었습니다! (딥러닝 모델 병합은 새벽에 진행됩니다)")
