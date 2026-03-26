import hashlib
import os
import time
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Qdrant 연결 (로컬 환경에서 직접 실행 시 기본 포트 6333 오픈되어 있음)
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

client = QdrantClient(url=QDRANT_URL, timeout=60)

def map_path(filepath):
    # Docker 내부의 리눅스 경로('/app/data')를 Windows 로컬 경로로 안전하게 매핑
    if filepath.startswith("/app/data"):
        return filepath.replace("/app/data", "data").replace("/", os.sep)
    return filepath

def compute_md5(filepath):
    try:
        with open(filepath, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    except Exception as e:
        return None

def migrate():
    print(f"[*] 데이터베이스 마이그레이터 시작 (Qdrant 단일화)")
    print(f"[*] 대상 컬렉션: {COLLECTION_NAME}")
    
    # 1. Qdrant에 해시 인덱스가 없다면 생성 (검색 O(1) 속도 보장)
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="hash",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        print("[+] 'hash' 필드 고속 검색 인덱스(Keyword) 생성 완료.")
    except Exception as e:
        # 이미 존재하면 넘어감
        print("[-] 'hash' 인덱스가 이미 존재하거나 생성 오류 (정상):", e)

    total_points = client.get_collection(COLLECTION_NAME).points_count
    print(f"\n[*] 총 스캔 대상: {total_points}장")
    
    offset = None
    processed = 0
    updated = 0
    missing = 0
    
    start_time = time.time()
    
    while True:
        records, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=500,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        batch_operations = []
        
        for point in records:
            processed += 1
            payload = point.payload or {}
            filepath = payload.get("filepath", "")
            
            # 이미 해시가 박혀있다면 패스 (재실행 시 멱등성 보장)
            if "hash" in payload and payload["hash"]:
                continue
                
            local_path = map_path(filepath)
            
            file_md5 = compute_md5(local_path)
            if file_md5:
                # 업서트할 페이로드 오퍼레이션 쌓기
                op = models.SetPayloadOperation(
                    set_payload=models.SetPayload(
                        payload={"hash": file_md5},
                        points=[point.id]
                    )
                )
                batch_operations.append(op)
            else:
                missing += 1
                
        # 배치가 찼으면 Qdrant 일괄(Bulk) Patch 요청
        if batch_operations:
            client.batch_update_points(
                collection_name=COLLECTION_NAME,
                update_operations=batch_operations
            )
            updated += len(batch_operations)
            
        print(f" >> 진행률: {processed}/{total_points} (현재 업데이트: {updated}장, 파일유실: {missing}장)", end="\r")
        
        offset = next_offset
        if offset is None:
            break

    elapsed = time.time() - start_time
    print(f"\n\n[🔥] 마이그레이션 압축 종료 (소요시간: {elapsed:.1f}초)")
    print(f" - 총 검사: {processed}장")
    print(f" - 새로 주입된 해시 갯수: {updated}장")
    print(f" - 파일을 찾을 수 없는 갯수: {missing}장")
    print("\n✅ Qdrant에 성공적으로 Hash가 주입되었습니다! 이제 SQLite는 멸망해도 됩니다.")

if __name__ == "__main__":
    migrate()
