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
        for res in points_data:
            p = getattr(res, 'payload', {})
            fpath = p.get("filepath")
            if fpath:
                similar_files.append(fpath)
                exif_str = get_physical_metadata_str(fpath)
                print(f"  [🕵️‍♂️ AUDIT-BEFORE (Time/Loc)] File: {fpath} | Loc: {p.get('location')} | Date: {p.get('date')} | People: {p.get('people')}")
                print(f"      ㄴ [메타데이터-BEFORE]: {exif_str}")
                try:
                    import json, os
                    with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                        tf.write(json.dumps({"type": "BEFORE", "hash_key": os.path.basename(fpath)[:15], "filepath": fpath, "location": p.get('location'), "date": p.get('date'), "people": p.get('people'), "exif": exif_str}, ensure_ascii=False) + "\n")
                except: pass
    else:
        print("[-] 지정된 타겟 포인트 리스트가 없습니다. 종료합니다.")
        return
    # ----------------------------------------------------
    # [1~2단계] 공용 PhotoPurger를 호출하여 기존 DB 제명 & 썸네일 파기 후 원본만 uploads_raw로 회수
    # ----------------------------------------------------
    from api.utils.photo_purger import PhotoPurger
    uploads_dir = "/app/data/uploads_raw"
    os.makedirs(uploads_dir, exist_ok=True)
    moved_files = []
    
    # zipped iteration: zip(similar_files, target_points) (개수가 같다고 보장될 때)
    # 하지만 더 안전하게는 각 파일별로 돌리는 것이 좋음
    for i, fpath in enumerate(similar_files):
        # 쌍을 이루는 Qdrant point_id 가 존재한다면 매핑
        pt_id = target_points[i] if i < len(target_points) else None
        
        # 통합 유틸리티를 호출하여 찌꺼기를 날리고 원본만 보존!
        PhotoPurger.purge_photo_data(
            abs_path=fpath, 
            point_id=pt_id, 
            keep_original=True
        )
        
        # 껍데기만 무사히 남은 원본 파일을 물리적으로 uploads_raw 이주
        if os.path.exists(fpath):
            base, ext = os.path.splitext(os.path.basename(fpath))
            trace_id = f"fbtrace_{uuid.uuid4().hex[:8]}"
            trace_dir = os.path.join(uploads_dir, trace_id)
            os.makedirs(trace_dir, exist_ok=True)
            safe_new_name = f"{base}_fbpass_{uuid.uuid4().hex[:8]}{ext}"
            new_fpath = os.path.join(trace_dir, safe_new_name)
            shutil.move(fpath, new_fpath)
            moved_files.append(new_fpath)
            
            try:
                import json
                with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                    tf.write(json.dumps({"type": "BEFORE", "trace_id": trace_id, "filepath": fpath, "location": p.get('location'), "date": p.get('date'), "people": p.get('people')}, ensure_ascii=False) + "\n")
            except: pass
            
    print(f"  [+] 총 {len(moved_files)}개의 원본 파일이 과거 기록을 청산하고 uploads_raw로 무사히 대피했습니다.")

    # ----------------------------------------------------
    # [3~4단계] 메타데이터 수정 독립형 모듈(MetadataEditor) 출동
    # ----------------------------------------------------
    if moved_files:
        from api.utils.metadata_editor import MetadataEditor
        MetadataEditor.stamp_metadata(moved_files, target_date, target_location)
        
        # ----------------------------------------------------
        # [5~6단계] Event Broadcasting (이후 Organizer -> Indexer 릴레이 자동 가동)
        # ----------------------------------------------------
        from core.events import publish_event
        publish_event("FileUploaded", {"source": "feedback_service_rebuild"})
        print("  [+] 새로운 메타데이터 정보가 이식되었습니다. 글로벌 파이프라인(Organizer->Indexer)을 트리거합니다.")


def process_face_enrollment(qdrant_id, known_name, target_points_str="[]"):
    print(f"[*] 인물 물리적 재학습 가동: 타겟 UUID {qdrant_id}, 학습 지정 이름: {known_name}")
    from qdrant_client import QdrantClient
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_str:
            target_points = json.loads(target_points_str)
    except Exception: pass
    
    # 1. 파일 시스템 복제 및 마이그레이션 (메타데이터 건너뜀)
    target_filepaths = []
    moved_files = []
    # --- [치명타 수술 완료] Qdrant에서 파일 경로와 함께 콕 집은 얼굴의 BBox(좌표)까지 통째로 가져옵니다 ---
    if target_points:
        points_data = client.retrieve(collection_name=COLLECTION_NAME, ids=target_points, with_payload=True)
        for res in points_data:
            filepath = res.payload.get("filepath")
            face_bbox = res.payload.get("face_bbox")
            if filepath and os.path.exists(filepath):
                exif_str = get_physical_metadata_str(filepath)
                print(f"  [🕵️‍♂️ AUDIT-BEFORE (Face)] File: {filepath} | Loc: {res.payload.get('location')} | Date: {res.payload.get('date')} | People: {res.payload.get('people')}")
                print(f"      ㄴ [메타데이터-BEFORE]: {exif_str}")
                target_filepaths.append({
                    "filepath": filepath,
                    "face_bbox": face_bbox,
                    "point_id": res.id,
                    "location": res.payload.get('location'),
                    "date": res.payload.get('date'),
                    "people": res.payload.get('people'),
                    "exif": exif_str
                })
                
    if not target_filepaths:
        print("  [!] 이동할 유효한 파일이 없습니다. 인물 학습을 중단합니다.")
        return
        
    enrolled_dir = os.path.join("/app/data/enrolled", known_name)
    os.makedirs(enrolled_dir, exist_ok=True)
    
    import shutil
    import cv2
    
    # 중복 파일 제어를 위해 filepath 기준 집합(Set) 대신 리스트 순회 (한 사진에 여러 명의 동일 타겟 얼굴이 잡힐 수도 있으므로 uuid 사용)
    for target in target_filepaths:
        filepath = target['filepath']
        face_bbox = target['face_bbox']
        point_id = target['point_id']
        
        # [롤백/재수정 자동화] 기존 다른 인물 폴더에 잘못 들어갔던 과거 파일(유령 조각)을 먼저 싹 쓸어버립니다.
        import glob
        old_ghosts = glob.glob(f"/app/data/enrolled/*/{point_id}.jpg")
        for ghost in old_ghosts:
            try: os.remove(ghost)
            except: pass
            
        # 1-1. enrolled 폴더로 '정확히 해당 타겟의 얼굴만' 크롭해서 복사 (데이터셋 오염 방지)
        filename = f"{point_id}.jpg"
        enrolled_dest = os.path.join(enrolled_dir, filename)
        
        if not os.path.exists(enrolled_dest):
            if face_bbox and len(face_bbox) == 4:
                try:
                    img = cv2.imread(filepath)
                    if img is not None:
                        x1, y1, x2, y2 = map(int, face_bbox)
                        h, w = img.shape[:2]
                        # 얼굴 인식을 위해 주변 문맥 여백(Margin) 20% 부여
                        margin_x = int((x2 - x1) * 0.2)
                        margin_y = int((y2 - y1) * 0.2)
                        nx1, ny1 = max(0, x1 - margin_x), max(0, y1 - margin_y)
                        nx2, ny2 = min(w, x2 + margin_x), min(h, y2 + margin_y)
                        
                        face_chip = img[ny1:ny2, nx1:nx2]
                        cv2.imwrite(enrolled_dest, face_chip)
                        print(f"  [+] 정밀 크롭(Crop) 데이터셋 축적 완료: {enrolled_dest}")
                    else:
                        raise Exception("cv2.imread failed")
                except Exception as e:
                    print(f"  [!] 얼굴 크롭 실패, 원본 전체 복사 대체: {e}")
                    shutil.copy2(filepath, enrolled_dest)
            else:
                shutil.copy2(filepath, enrolled_dest)
            
        # [치명적 버그 수정: 장소 메타데이터 증발 방지]
        # 폴더명(예: 2021-10_서울)에 의존하고 EXIF GPS가 없는 사진이 uploads_raw로 이주 시 '위치정보없음'으로 전락하는 것을 방지!
        parent_dir = os.path.basename(os.path.dirname(filepath))
        if "_" in parent_dir:
            parts = parent_dir.split("_", 1)
            if len(parts) > 1 and parts[1] not in ["Unknown-Location", "위치정보없음", "Unknown-Year"]:
                presumed_date = parts[0]
                presumed_loc = parts[1]
                try:
                    from api.utils.metadata_editor import MetadataEditor
                    # 날짜와 장소 메타데이터를 원본에 영구 삽입 (exiftool)
                    MetadataEditor.stamp_metadata([filepath], target_date=presumed_date, target_location=presumed_loc)
                    print(f"  [+] EXIF 없는 파일의 메타데이터 영구 보존 조치 완료({presumed_date}, {presumed_loc}): {filepath}")
                except Exception as e:
                    print(f"  [-] EXIF 지역 보존 실패: {e}")
            
        # 1-2. 기존 찌꺼기 완전 파기 (Qdrant & SQLite DELETED)
        # 여러 얼굴이 하나의 사진에 있을 수 있으므로 동일 파일의 중복 처리를 방지하기 위해 try-except로 무시
        try: PhotoPurger.purge_photo_data(filepath, point_id=point_id, keep_original=True)
        except Exception as e: print(f"  [!] Photo purge failed: {e}")
        
        # 1-3. 유령 파일(Ghost)이 되지 않도록 새 생명을 부여하며 uploads_raw 큐로 이주
        # 비교 로그 추적을 위해 특수 trace 폴더에 담아서 보냅니다.
        trace_id = f"fbtrace_{uuid.uuid4().hex[:8]}"
        trace_dir = os.path.join("/app/data/uploads_raw", trace_id)
        os.makedirs(trace_dir, exist_ok=True)
        raw_dest = os.path.join(trace_dir, os.path.basename(filepath))
        if os.path.exists(filepath):
            shutil.move(filepath, raw_dest)
            print(f"  [+] 타겟 사진 재인덱싱 대기열 이동 완료: {raw_dest}")
            moved_files.append(raw_dest)
            
            # Trace DB 기록 (AUDIT 용)
            try:
                with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                    tf.write(json.dumps({"type": "BEFORE", "trace_id": trace_id, "filepath": filepath, "location": target.get("location"), "date": target.get("date"), "people": target.get("people"), "exif": target.get("exif", "")}, ensure_ascii=False) + "\n")
            except: pass
            
    if target_filepaths:
        # 2. 얼굴 도감 정밀 리빌드 (InsightFace)
        print("  [*] 딥러닝 인물 도감 전체 재학습 시작 (InsightFace VRAM 가동)...")
        import cv2
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
                    
                    best_face = sorted(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)[0]
                    person_vectors.append(best_face.normed_embedding)
                    
                if person_vectors:
                    mean_vec = np.mean(person_vectors, axis=0)
                    mean_vec = mean_vec / np.linalg.norm(mean_vec)
                    new_known_faces[person_name] = mean_vec.tolist()
                    print(f"    - '{person_name}' 님 학습 완료 ({len(person_vectors)}장 통합본)")
                    
        with open(KNOWN_FACES_PATH, 'wb') as f:
            pickle.dump(new_known_faces, f)
        print(f"  [+] 온디맨드 인물 도감 교체 완료! (총 {len(new_known_faces)}명)")
        
        # 3. 새 도감을 바탕으로 재인덱싱 글로벌 트리거 가동
        from core.events import publish_event
        publish_event("FileUploaded", {"source": "feedback_face_rebuild"})
        print("  [+] 인물 학습 종료. 글로벌 파이프라인(Organizer->Indexer)을 스케줄링합니다.")
