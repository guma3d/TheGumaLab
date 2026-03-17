import time
import os
import random
from vector_indexer import VectorIndexer, COLLECTION_NAME

print("== 1. ONNX GPU Check ==")
import onnxruntime as ort
print("ONNX Providers:", ort.get_available_providers())

indexer = VectorIndexer()

# Make sure existing DB is clean
print("== 2. Wipe existing data ==")
try:
    indexer.q_client.delete_collection(COLLECTION_NAME)
    indexer.init_qdrant_collection()
    indexer.cursor.execute("DELETE FROM vectorized_files")
    indexer.conn.commit()
    # Find all .xmp and delete
    for root, dirs, files in os.walk("/app/data/organized"):
        for f in files:
            if f.endswith('.xmp'):
                os.remove(os.path.join(root, f))
except Exception as e:
    print("Cleanup err:", e)

print("== 3. Run VectorIndexer ==")
t0 = time.time()
indexer.run(test_limit=100)
t1 = time.time()
elapsed = t1 - t0

print(f"\n=============================================")
print(f"[성능 테스트 결과] 100장 처리 완료!")
print(f"총 소요 시간: {elapsed:.2f}초")
print(f"1장당 평균 속도: {elapsed/100:.2f}초")
print(f"=============================================\n")

print("== 4. Fetch 5 random payloads from Qdrant ==")
# Scroll
res = indexer.q_client.scroll(
    collection_name=COLLECTION_NAME,
    limit=5,
    with_payload=True,
    with_vectors=False
)

points = res[0]
for idx, p in enumerate(points):
    print(f"\n--- 샘플 {idx+1} ---")
    payload = p.payload
    print(f"파일명: {payload.get('filename')}")
    print(f"시간대/계절: {payload.get('time_of_day')} / {payload.get('season')}")
    print(f"사람/얼굴수: {payload.get('people')} ({payload.get('face_count')}명)")
    print(f"위치/날짜: {payload.get('location')} / {payload.get('date')}")
    print(f"사물태그: {payload.get('objects')}")
    print(f"캡션: {payload.get('caption')}")
    if payload.get('face_count', 0) > 0:
        print(f"주요인물 나이/성별/감정: {payload.get('age')}, {payload.get('gender')}, {payload.get('emotion')}")
        
print("\n== 5. Cleanup Generated Data ==")
try:
    indexer.q_client.delete_collection(COLLECTION_NAME)
    indexer.init_qdrant_collection()
    indexer.cursor.execute("DELETE FROM vectorized_files")
    indexer.conn.commit()
    for root, dirs, files in os.walk("/app/data/organized"):
        for f in files:
            if f.endswith('.xmp'):
                os.remove(os.path.join(root, f))
    print("Cleaned up successfully.")
except Exception as e:
    print("Cleanup err:", e)
