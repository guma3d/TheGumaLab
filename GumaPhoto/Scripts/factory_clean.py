import os
import requests

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

# 1. Qdrant 컬렉션 삭제 명령 (모든 데이터 백지화)
print("\n[AI 엔진] 기존 AI 벡터 데이터베이스 영구 삭제 중...")
try:
    resp = requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", timeout=120)
    if resp.status_code in [200, 201, 202, 404]: 
        print(" -> ✅ Qdrant 벡터 DB 파기(초기화) 성공!")
    else:
        print(f" -> ❌ DB 삭제 실패: HTTP {resp.status_code} - {resp.text}")
        exit(1)
except Exception as e:
    print(f" -> ❌ Qdrant 서버 통신 실패: {e}")
    exit(1)

print(" -> 컨테이너 내부 데이터베이스 초기화 완료.")
