import os
import xmp_utils
from qdrant_client import QdrantClient

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6337")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

def run():
    print("[*] 기존 Qdrant DB의 모든 데이터를 조회하여 누락된 과거 사진들의 XMP 파일을 일괄 자동 생성합니다...")
    try:
        client = QdrantClient(url=QDRANT_URL)
    except Exception as e:
        print(f"Qdrant 연결 실패: {e}")
        return
        
    offset = None
    limit = 500
    total = 0
    missing_files = 0
    
    while True:
        try:
            res = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            points, next_page_offset = res
            
            for point in points:
                payload = point.payload
                filepath = payload.get("filepath")
                # 파일이 실제로 존재할 때만 사이드카 XMP를 생성합니다
                if filepath and os.path.exists(filepath):
                    xmp_utils.generate_xmp_sidecar(filepath, payload)
                    total += 1
                else:
                    missing_files += 1
                    
            print(f"  - 스캔 및 XMP 생성 진행중... (현재 {total}장 복구 완료)")
            
            if next_page_offset is None:
                break
            offset = next_page_offset
        except Exception as batch_error:
            print(f"배치 조회 중 에러: {batch_error}")
            break
            
    print(f"\n✅ 과거에 누락되었던 총 {total}장 사진들의 XMP 영구 백업(덮어쓰기) 조치가 완료되었습니다!")
    if missing_files > 0:
        print(f"⚠️ 디스크에 원본 사진이 없어 XMP를 생성하지 못하고 건너뛴 파일 개수: {missing_files}개")

if __name__ == "__main__":
    run()
