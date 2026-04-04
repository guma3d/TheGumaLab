import os
import shutil
import json
import subprocess
import pickle
import uuid
import numpy as np
from qdrant_client import QdrantClient

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
            return f"GPS: {gps} | Date: {d.get('DateTimeOriginal', 'None')}"
    except Exception as e: pass
    return "EXIF: Parse Error or Empty"

def process_time_location_feedback(qdrant_id: str, target_date: str, target_location: str, target_points_str: str = "[]", old_snapshots_json: str = "[]"):
    print(f"🔄 [Celery/Worker] 시간/장소 피드백 메타데이터 수정 태스크 시작 (ID: {qdrant_id})")
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
    
    # 0. 라우터에서 전달받은 스냅샷(BEFORE)을 활용하여 도플갱어 이슈 차단
    old_snapshots = []
    try:
        old_snapshots = json.loads(old_snapshots_json)
    except: pass
    snapshot_map = {str(item["id"]): item for item in old_snapshots}
        
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
                rid = str(res.id)
                old_data = snapshot_map.get(rid, {})
                valid_targets.append({
                    "fpath": fpath, 
                    "pt_id": res.id,
                    "old_location": old_data.get('location', p.get('location')),
                    "old_date": old_data.get('date', p.get('date')),
                    "old_geo_point": old_data.get('geo_point', p.get('geo_point'))
                })
                exif_str = get_physical_metadata_str(fpath)
                print(f"  [🕵️‍♂️ AUDIT-BEFORE (Time/Loc)] File: {fpath} | Loc: {old_data.get('location')} | Date: {old_data.get('date')} | People: {old_data.get('people')}")
                print(f"      ㄴ [메타데이터-BEFORE]: {exif_str}")
                try:
                    with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                        tf.write(json.dumps({"type": "BEFORE", "trace_id": res.id, "hash_key": os.path.basename(fpath)[:15], "filepath": fpath, "location": old_data.get('location'), "geo_point": old_data.get('geo_point'), "date": old_data.get('date'), "people": old_data.get('people'), "exif": exif_str}, ensure_ascii=False) + "\n")
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
                from api.utils.metadata_parser import MetadataParser
                final_osm_name = MetadataParser.parse_location(lat_val, lon_val)
                target_location = f"[{lat_val}, {lon_val}] {final_osm_name}"
                print(f"  [📍 피드백 일관성 통합] 카카오 '{raw_place}' ➡️ OSM 메타데이터 통합 '{final_osm_name}'")
            except Exception as e:
                print(f"  [-] 통합 OSM 메타데이터 파서 실패(원본 유지): {e}")

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
                    if "old_geo_point" in tg:
                        rb_payload["geo_point"] = tg.get("old_geo_point")
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
        payload_update = {}
        if target_location and "Unknown" not in target_location:
            import re
            match = re.search(r'^\[([-\d\.]+),\s*([-\d\.]+)\]\s*(.*)$', target_location)
            if match:
                lat_val = float(match.group(1))
                lon_val = float(match.group(2))
                clean_target_location = str(match.group(3)).strip()
                payload_update["geo_point"] = {"lat": lat_val, "lon": lon_val}
            payload_update["location"] = clean_target_location
            
        if target_date and "Unknown" not in target_date:
            from api.utils.metadata_parser import MetadataParser
            time_of_day, season = MetadataParser.parse_time_and_season(date_val=target_date)
            payload_update["date"] = target_date
            if time_of_day != "Unknown": payload_update["time_of_day"] = time_of_day
            if season != "Unknown": payload_update["season"] = season
            
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
                        "geo_point": ap.get('geo_point') if 'ap' in locals() else None,
                        "exif": exif_str
                    }, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"      [!] 시스템 로그 갱신 중 에러 (무시): {e}")
            
        try:
            from api.services.theme_service import build_timeline_cache_only
            build_timeline_cache_only()
        except Exception as e:
            print(f"      [!] 타임라인 캐시 동기화 콜백 에러: {e}")
        
        print("  [+] 메타데이터 EXIF 주입 및 DB 덮어쓰기가 초고속으로 완료되었습니다!")


def process_face_enrollment(qdrant_id: str, known_name: str, target_points_json: str = "[]", skip_enrolled_learning: bool = False):
    print(f"[*] 인물 물리적 재학습 가동: 메인 UUID {qdrant_id}, 학습 지정 이름: {known_name}")
    from qdrant_client import QdrantClient
    client = QdrantClient(QDRANT_URL)
    
    target_points = []
    try:
        if target_points_json:
            target_points = json.loads(target_points_json)
    except Exception: pass
    
    if qdrant_id and qdrant_id not in target_points:
        target_points.append(qdrant_id)
    
    target_filepaths = []
    if target_points:
        points_data = client.retrieve(collection_name=COLLECTION_NAME, ids=target_points, with_payload=True, with_vectors=True)
        for res in points_data:
            filepath = res.payload.get("filepath")
            face_bbox = res.payload.get("face_bbox")
            if filepath and os.path.exists(filepath):
                target_filepaths.append({
                    "filepath": filepath,
                    "face_bbox": face_bbox,
                    "point_id": res.id,
                    "old_people": res.payload.get("people", []),
                    "vector": res.vector
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
                with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                    tf.write(json.dumps({"type": "BEFORE", "trace_id": point_id, "filepath": filepath, "people": target.get("old_people", [])}, ensure_ascii=False) + "\n")
                    tf.write(json.dumps({"type": "AFTER", "trace_id": point_id, "filepath": filepath, "people": [true_name]}, ensure_ascii=False) + "\n")
            except: pass
            print(f"    - {os.path.basename(filepath)} : 업데이트 완료 [{true_name}]")
        return
        
    best_folder_name = known_name
    
    # --- 스마트 라우팅 로직 (Cosine Similarity 기반) ---
    known_faces_data = {}
    pkl_path = "/app/data/known_faces.pkl"
    raw_faces = {}
    if os.path.exists(pkl_path):
        import pickle
        import numpy as np
        try:
            with open(pkl_path, "rb") as f:
                raw_faces = pickle.load(f)
                for name, vectors in raw_faces.items():
                    if vectors:
                        vec_array = np.array(vectors)
                        mean_vec = vec_array if vec_array.ndim == 1 else np.mean(vec_array, axis=0)
                        mean_vec = mean_vec / np.linalg.norm(mean_vec)
                        known_faces_data[name] = mean_vec
        except Exception as e: 
            print(f"  [!] 스마트 라우팅을 위한 known_faces.pkl 로딩 실패: {e}")

    candidates = [n for n in known_faces_data.keys() if n == known_name or n.startswith(f"{known_name}_")]
    best_folder_name = known_name
    
    main_target = next((item for item in target_filepaths if item["point_id"] == qdrant_id), target_filepaths[0])
    vec_data = main_target.get("vector")
    
    face_vec = None
    if isinstance(vec_data, dict):
        face_vec = vec_data.get("face") or vec_data.get("scene")
    elif vec_data:
        face_vec = vec_data
        
    face_bbox = main_target.get('face_bbox')
    learnable = True
    if skip_enrolled_learning:
        learnable = False
        print("  [🛡️ 수동 보호] 사용자가 'Send But NoFeedback'을 요청했습니다. 딥러닝 enrolled 등록을 건너뜁니다.")
    elif face_bbox and len(face_bbox) == 4:
        bw = face_bbox[2] - face_bbox[0]
        bh = face_bbox[3] - face_bbox[1]
        
        # InsightFace 최적 입력 크기는 112x112. 100px 미만인 아주 흐릿한 군중 속 얼굴만 딥러닝 오염 방지를 위해 스킵합니다.
        if bw < 100 or bh < 100:
            learnable = False
            print(f"  [🛡️ 딥러닝 보호] BBox 크기({int(bw)}x{int(bh)})가 100px 미만이므로, 품질 보호를 위해 enrolled 등록 및 실시간 벡터 주입을 스킵합니다.")
    else:
        learnable = False
        
    if learnable:
        if len(candidates) >= 1:
            print(f"  [*] '{known_name}' 관련 폴더가 {len(candidates)}개 발견되었습니다. 가장 유사한 얼굴 중심점(Centroid)을 찾습니다...")
            if face_vec:
                import numpy as np
                face_vec_np = np.array(face_vec)
                face_vec_np = face_vec_np / np.linalg.norm(face_vec_np)
                
                best_sim = -1.0
                for cand in candidates:
                    sim = float(np.dot(face_vec_np, known_faces_data[cand]))
                    print(f"    - 후보 [{cand}] 유사도: {sim:.4f}")
                    if sim > best_sim:
                        best_sim = sim
                        best_folder_name = cand
                print(f"  [+] 최고 유사도 후보 방: {best_folder_name} (유사도 {best_sim:.4f})")
                
                # [Multi-Centroid Logic] 다중 중심점 동적 생성 (유사도 0.35 미만이면 새 폴더 개척)
                if best_sim > 0.0 and best_sim < 0.35:
                    new_cand_idx = len(candidates)
                    best_folder_name = f"{known_name}_{new_cand_idx}"
                    print(f"  [🧬 다중 중심점 분열] 얼굴이 기존 기억(유사도 {best_sim:.4f})과 너무 다릅니다! 동일인물의 완전히 새로운 앵커를 위해 '{best_folder_name}' 폴더를 파생 개척합니다.")
                    
        # [Zero-Latency Realtime Vector Injection] 새벽 3시 딥러닝 우회 즉시 캐싱
        if face_vec and len(face_vec) >= 128:
            import pickle
            if best_folder_name not in raw_faces:
                raw_faces[best_folder_name] = []
            raw_faces[best_folder_name].append(face_vec)
            try:
                with open(pkl_path, "wb") as f:
                    pickle.dump(raw_faces, f)
                print(f"  [⚡ Zero-Latency 학습 완료] '{best_folder_name}' 중심점 네트워크에 방금 피드백된 얼굴 벡터를 즉시 병합했습니다!")
            except Exception as e:
                print(f"  [-] 실시간 벡터 주입 실패 (다음 새벽에 일괄 처리됩니다): {e}")
        
        enrolled_dir = os.path.join("/app/data/enrolled", best_folder_name)
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
                        margin_x = int((x2 - x1) * 0.1)
                        margin_y = int((y2 - y1) * 0.1)
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
            with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                tf.write(json.dumps({"type": "BEFORE", "trace_id": point_id, "filepath": filepath, "people": target.get("old_people", [])}, ensure_ascii=False) + "\n")
                tf.write(json.dumps({"type": "AFTER", "trace_id": point_id, "filepath": filepath, "people": [known_name]}, ensure_ascii=False) + "\n")
        except: pass
        
        print(f"    - {os.path.basename(filepath)} : 영구 업데이트 완료 [{known_name}]")
        
    try:
        from api.services.theme_service import build_timeline_cache_only
        build_timeline_cache_only()
    except Exception as e:
        print(f"  [!] 타임라인 캐시 동기화 콜백 에러: {e}")
        
    print("  [+] 인물 사진 도감 축적 및 DB 반영 모두 완료되었습니다! (딥러닝 모델 병합은 새벽에 진행됩니다)")
