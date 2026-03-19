import os
import time
from vector_indexer import VectorIndexer, COLLECTION_NAME

print("[*] 실행 중... 데이터를 초기화합니다.")
try:
    indexer = VectorIndexer()

    # 1. Qdrant 벡터 삭제
    try:
        indexer.q_client.delete_collection(COLLECTION_NAME)
        time.sleep(1)
        print("  - Qdrant 컬렉션 삭제 완료")
    except Exception as e:
        print("  - Qdrant 컬렉션 삭제 무시 (존재하지 않음):", e)
        
    indexer.init_qdrant_collection()
    print("  - Qdrant 빈 컬렉션 재구축 완료")

    # 2. SQLite 상태 기록 삭제
    indexer.cursor.execute("DELETE FROM vectorized_files")
    indexer.conn.commit()
    print("  - SQLite vectorized_files 진행 기록 모두 삭제 완료")

    # 3. 물리적 XMP 타임라인 파일 삭제
    count = 0
    for root, dirs, files in os.walk("/app/data/organized"):
        for f in files:
            if f.endswith('.xmp'):
                os.remove(os.path.join(root, f))
                count += 1
                
    print(f"  - 찌꺼기 XMP 사이드카 파일 총 {count}개 폭파 완료")

    print("\n✅ 모든 데이터가 깨끗한 초기 상태로 돌아갔습니다!")
except Exception as e:
    print(f"\n🚨 치명적 오류 발생: {e}")
