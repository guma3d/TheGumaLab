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

def process_time_location_feedback(qdrant_id, target_date, target_location):
    print(f"[*] 시간/장소 피드백 가동: 타겟 UUID {qdrant_id}, 새로운 시간: {target_date}, 새로운 장소: {target_location}")
    client = QdrantClient(QDRANT_URL)
    
    # 1. 1장 원본의 시각 분위기 공간 벡터(scene/SigLIP) 획득
    records = client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[qdrant_id],
        with_vectors=True,
        with_payload=True
    )
    if not records:
        print("[-] 대상 사진을 Qdrant에서 찾을 수 없습니다.")
        return
        
    pt = records[0]
    vecs = pt.vector
    scene_vector = vecs.get("scene") if isinstance(vecs, dict) else vecs
    if not scene_vector:
        print("[-] scene (SigLIP) 벡터가 없습니다.")
        return
        
    # 2. Qdrant 벡터 서치를 통해 동일한 시공간(유사도 90% 이상)의 그룹핑 N장 추출
    search_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=scene_vector,
        using="scene",
        limit=50,
        score_threshold=0.8,
        with_payload=True
    ).points
    
    similar_files = [res.payload.get("filepath") for res in search_res if res.payload.get("filepath")]
    print(f"  [+] 동일 시간/장소 집단 {len(similar_files)}장 클러스터링 감지 완료.")
    
    # 3. EXIF 불변의 데이터 하드코딩 (향후 piexif 모듈 개발 구간)
    print("  [+] EXIF Hardcoding 준비 중...")
    for fpath in similar_files:
        # TODO: piexif.load -> date/location 수정 -> piexif.insert 반영
        pass

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
    
    print("[*] 향후 vector_indexer.py 가 이 폴더들을 신선하게 재스캔 할 것입니다.")

def process_face_enrollment(qdrant_id, known_name):
    print(f"[*] 인물 피드백 가동: 타겟 얼굴 UUID {qdrant_id}, 새로운 이름: {known_name}")
    client = QdrantClient(QDRANT_URL)
    
    # 1. Unknown 얼굴 벡터(v_face/InsightFace 512D) 획득
    records, _ = client.scroll(COLLECTION_NAME, scroll_filter={"must": [{"key": "id", "match": {"value": qdrant_id}}]}, limit=1, with_vectors=True, with_payload=True)
    if not records: return
    
    face_vector = records[0].vector.get("v_face")
    if not face_vector: return
    
    # 2. 가장 똑같은 512D 벡터를 지닌 여러 Unknown 얼굴 사진 추출 
    search_res = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=("v_face", face_vector),
        limit=50,
        score_threshold=0.85, # 85% 이상 비슷한 얼굴
        with_payload=True
    )
    
    face_vectors = [res.vector.get("v_face") for res in search_res if "v_face" in res.vector]
    
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
    args = parser.parse_args()
    
    if args.type == "time_loc":
        process_time_location_feedback(args.doc_id, args.date, args.loc)
    elif args.type == "face":
        process_face_enrollment(args.doc_id, args.name)
