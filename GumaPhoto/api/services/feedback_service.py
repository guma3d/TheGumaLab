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
                valid_targets.append({"fpath": fpath, "pt_id": res.id})
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
    # [1단계] 메타데이터 수정 (EXIF 영구 변경)
    # ----------------------------------------------------
    valid_filepaths = [item["fpath"] for item in valid_targets]
    if valid_filepaths:
        from api.utils.metadata_editor import MetadataEditor
        MetadataEditor.stamp_metadata(valid_filepaths, target_date, target_location)
        print(f"  [+] 총 {len(valid_filepaths)}개의 원본 파일 메타데이터(EXIF)가 성공적으로 덮어쓰기 완료되었습니다.")
        
        # ----------------------------------------------------
        # [2단계] Qdrant 덮어쓰기를 위해 벡터인덱서 모듈 단일 호출
        # (장소, 시간 피드백이므로 InsightFace 제외)
        # ----------------------------------------------------
        import sys
        if "/app" not in sys.path:
            sys.path.append("/app")
        from vector_indexer import VectorIndexer
        
        print("  [*] 변경된 메타데이터를 바탕으로 벡터 정보를 Qdrant에 덮어씁니다...")
        idx_bot = VectorIndexer(skip_face=True)
        
        # Qdrant 페이로드용 장소 이름 정제 ([lat, lon] 부분 제거)
        clean_target_location = target_location
        if target_location:
            import re
            match = re.search(r'^\[([-\d\.]+),\s*([-\d\.]+)\]\s*(.*)$', target_location)
            if match:
                clean_target_location = str(match.group(3)).strip()
                
        idx_bot.force_reindex_files(valid_filepaths, force_location=clean_target_location, force_date=target_date)        
        # Qdrant에 저장된 최신 값을 다시 불러와 시스템 Audit 로그에 정확히 남김
        # (기존 target_date 파라미터가 "Unknown Date"일 경우, 사용자가 오해하지 않도록 실데이터 추출)
        try:
            client = QdrantClient(QDRANT_URL)
            with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                for tg in valid_targets:
                    # 방금 업데이트 완료된 Qdrant 최신 페이로드 조회
                    after_pts = client.retrieve(collection_name=COLLECTION_NAME, ids=[tg["pt_id"]], with_payload=True)
                    if after_pts:
                        ap = after_pts[0].payload or {}
                        after_date = ap.get('date', target_date)
                        after_loc = ap.get('location', target_location)
                    else:
                        after_date, after_loc = target_date, target_location
                        
                    exif_str = get_physical_metadata_str(tg["fpath"])
                    tf.write(json.dumps({
                        "type": "AFTER", 
                        "trace_id": tg["pt_id"], 
                        "filepath": tg["fpath"], 
                        "location": after_loc, 
                        "date": after_date,
                        "people": ap.get('people'),
                        "exif": exif_str
                    }, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"      [!] 시스템 로그 갱신 중 에러 (무시): {e}")
        
        print("  [+] 새로운 메타데이터 기반 벡터인덱싱 및 DB 덮어쓰기가 완료되었습니다!")


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
                    print(f"  [+] 정밀 크롭(Crop) 데이터셋 축적 완료: {enrolled_dest}")
            except Exception as e:
                print(f"  [!] 얼굴 크롭 실패: {e}")
                shutil.copy2(main_filepath, enrolled_dest)
        else:
            shutil.copy2(main_filepath, enrolled_dest)

    # 2. 얼굴 도감 정밀 리빌드
    print("  [*] 딥러닝 인물 도감 전체 재학습 시작...")
    from insightface.app import FaceAnalysis
    face_app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    
    new_known_faces = {}
    base_enrolled_dir = "/app/data/enrolled"
    if os.path.exists(base_enrolled_dir):
        for person_name in os.listdir(base_enrolled_dir):
            person_folder = os.path.join(base_enrolled_dir, person_name)
            if not os.path.isdir(person_folder): continue
            
            person_vectors = []
            for img_name in os.listdir(person_folder):
                img_path = os.path.join(person_folder, img_name)
                img = cv2.imread(img_path)
                if img is None: continue
                faces = face_app.get(img)
                if not faces: continue
                
                img_h, img_w = img.shape[:2]
                cx, cy = img_w / 2, img_h / 2
                best_face = sorted(faces, key=lambda f: ((f.bbox[0]+f.bbox[2])/2 - cx)**2 + ((f.bbox[1]+f.bbox[3])/2 - cy)**2)[0]
                person_vectors.append(best_face.normed_embedding)
                
            if person_vectors:
                mean_vec = np.mean(person_vectors, axis=0)
                mean_vec = mean_vec / np.linalg.norm(mean_vec)
                new_known_faces[person_name] = [mean_vec.tolist()]
                print(f"    - '{person_name}' 님 학습 완료 ({len(person_vectors)}장)")
                
    with open(KNOWN_FACES_PATH, 'wb') as f:
        pickle.dump(new_known_faces, f)
    print(f"  [+] 온디맨드 인물 도감 교체 완료! (총 {len(new_known_faces)}명)")
    
    # 메모리 회수
    del face_app
    
    # 3. 모든 대상 사진에 대해 InsightFace 평가 및 DB 덮어쓰기 실시
    print("  [*] 대상 사진 전체에 대해 독립형 InsightFace 적용 및 Qdrant 덮어쓰기...")
    from api.services.insightface_service import InsightFaceModule
    face_bot = InsightFaceModule()
    
    for target in target_filepaths:
        filepath = target['filepath']
        point_id = target['point_id']
        try:
            face_res = face_bot.analyze_image(filepath)
            
            client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={
                    "people": face_res["found_people"],
                    "face_count": face_res["face_count"],
                    "age": face_res["payload"].get("age"),
                    "gender": face_res["payload"].get("gender"),
                    "emotion": face_res["payload"].get("emotion"),
                },
                points=[point_id]
            )
            
            if "face" in face_res["vectors"]:
                from qdrant_client.models import PointVectors
                client.update_vectors(
                    collection_name=COLLECTION_NAME,
                    points=[PointVectors(id=point_id, vector={"face": face_res["vectors"]["face"]})]
                )
                
            try:
                with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                    tf.write(json.dumps({"type": "BEFORE", "trace_id": point_id, "filepath": filepath, "people": target.get("old_people", [])}, ensure_ascii=False) + "\n")
                    tf.write(json.dumps({"type": "AFTER", "trace_id": point_id, "filepath": filepath, "people": face_res["found_people"]}, ensure_ascii=False) + "\n")
            except: pass
            
            print(f"    - {os.path.basename(filepath)} : 업데이트 완료 {face_res['found_people']}")
        except Exception as e:
            print(f"    - {filepath} 덮어쓰기 실패: {e}")
            
    print("  [+] 인물 학습 및 DB 반영 모두 완료되었습니다!")
