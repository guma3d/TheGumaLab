import os
import sys
import subprocess
import cv2
import json
import logging

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

print(colors.OKBLUE + "="*60 + colors.ENDC)
print(colors.BOLD + "  [PHASE 1] 인물 딥러닝 등록(Enrolled) 도감 최신화 가동..." + colors.ENDC)
print(colors.OKBLUE + "="*60 + colors.ENDC)

try:
    ret = subprocess.run([sys.executable, "/app/Scripts/train_faces.py"])
    if ret.returncode != 0:
        print(colors.FAIL + "❌ [오류] 도감 재학습 중 치명적 오류가 발생했습니다. 프로세스를 중단합니다." + colors.ENDC)
        sys.exit(1)
except Exception as e:
    print(colors.FAIL + f"❌ [오류] {e}" + colors.ENDC)
    sys.exit(1)

print("\n" + colors.OKBLUE + "="*60 + colors.ENDC)
print(colors.BOLD + "  [PHASE 2] DB 내 미분류(Unknown Person) 상태인 파일 수색 및 핀포인트 추적..." + colors.ENDC)
print(colors.OKBLUE + "="*60 + colors.ENDC)

from qdrant_client import QdrantClient

logging.getLogger("httpx").setLevel(logging.WARNING)

print("[*] Qdrant 및 모델 초기화 중...")
qdrant = QdrantClient("http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

all_unknown_pts = []
offset = None
while True:
    try:
        results, offset = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=2000,
            with_payload=True,
            with_vectors=True,
            offset=offset
        )
    except Exception as e:
        print(colors.FAIL + f"❌ Qdrant 연결 오류: {e}" + colors.ENDC)
        sys.exit(1)
        
    for r in results:
        people = r.payload.get("people", [])
        is_unknown = False
        if not people:
            is_unknown = True
        else:
            for p in people:
                if "Unknown" in p or "No People" in p or "Unidentifiable" in p:
                    is_unknown = True
                    break
                    
        if is_unknown:
            filepath = r.payload.get("filepath")
            if filepath and os.path.exists(filepath):
                all_unknown_pts.append({
                    "id": r.id, 
                    "filepath": filepath,
                    "payload": r.payload,
                    "vectors": r.vector
                })
    if offset is None:
        break

total_targets = len(all_unknown_pts)
print(colors.OKGREEN + f"[*] 총 {total_targets}장의 타겟 미분류 사진을 확보했습니다! (스캔 재돌입)" + colors.ENDC)

if total_targets > 0:
    sys.path.append("/app")
    try:
        from api.services.indexer.model_faces import FaceEngine
    except ImportError as e:
        print(colors.FAIL + f"❌ FaceEngine import 실패: {e}" + colors.ENDC)
        sys.exit(1)
        
    face_engine = FaceEngine()
    success_count = 0
    
    for idx, item in enumerate(all_unknown_pts):
        point_id = item["id"]
        filepath = item["filepath"]
        payload = item["payload"]
        vectors = item["vectors"]
        
        cv_img = cv2.imread(filepath)
        if cv_img is None:
            continue
            
        print(f"\n  [{idx+1}/{total_targets}] 분석 중: {os.path.basename(filepath)}")
        
        try:
            face_count, found_people, best_face_vector, best_face_payload, real_age = face_engine.analyze_face(cv_img, filepath)
            
            if found_people and all(p not in ["Unknown People", "No People", "Unknown Person", "Unknown"] for p in found_people):
                print(colors.OKGREEN + f"    ✨ 빙고! 숨겨진 인물을 찾아냈습니다: {found_people}" + colors.ENDC)
                print(f"    👉 기존 등록 정보: {payload.get('people')} ➡️ 변경됨")
                
                # [🚨 긴급 롤백(Rollback) 대비 완벽 백업 보존]
                try:
                    import copy
                    with open("/app/data/face_hunter_rollback.jsonl", "a", encoding="utf-8") as rbf:
                        rbf.write(json.dumps({
                            "id": point_id,
                            "payload": payload,
                            "vectors": vectors
                        }, ensure_ascii=False) + "\n")
                except Exception as rbf_err:
                    print(colors.WARNING + f"      (백업 경고: {rbf_err})" + colors.ENDC)

                payload["people"] = found_people
                payload["face_count"] = face_count
                payload.update(best_face_payload)
                
                if best_face_vector:
                    if isinstance(vectors, dict):
                        vectors["face"] = best_face_vector
                    else:
                        vectors = {"face": best_face_vector}
                
                from qdrant_client.http.models import PointStruct
                new_point = PointStruct(id=point_id, vector=vectors, payload=payload)
                qdrant.upsert(collection_name=COLLECTION_NAME, points=[new_point])
                success_count += 1
                
                trace_file = "/app/data/audit_trace.json"
                try:
                    with open(trace_file, "a", encoding="utf-8") as wf:
                        wf.write(json.dumps({
                            "type": "AUTO_HUNTER",
                            "trace_id": f"hunter_{point_id}",
                            "filepath": filepath,
                            "date": payload.get('date'),
                            "location": payload.get('location'),
                            "people": found_people,
                            "exif": "Auto Face Hunter Batch Update"
                        }, ensure_ascii=False) + "\n")
                except: pass
            else:
                if not found_people or "No People" in found_people:
                    print(f"    - (인물 없음)")
                else:
                    print(f"    - (새로운 도감 벡터로도 여전히 미확인 인물입니다: {found_people})")
        except Exception as scan_err:
             print(colors.FAIL + f"    ❌ 이미지 스캔 중 에러 발생: {scan_err}" + colors.ENDC)
                
    print(colors.OKBLUE + f"\n✅ 스캔 종료! 총 {total_targets}장 중 {success_count}명의 숨겨진 요원의 신원을 밝혀내어 DB를 갱신했습니다!" + colors.ENDC)
else:
    print(colors.OKGREEN + "✅ 이미 미분류 인물이 없거나 실제 사진이 존재하지 않습니다." + colors.ENDC)

print(colors.OKBLUE + "\n========================================================" + colors.ENDC)
print(colors.BOLD + "  모든 헌터 작업이 종료되었습니다. 창을 닫으셔도 좋습니다." + colors.ENDC)
print(colors.OKBLUE + "========================================================" + colors.ENDC)
