import os
import requests

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

print("====================================================")
print(" 🛑 GumaPhoto 전면 초기화 (Factory Reset) 도구 🛑 ")
print("====================================================")
print(f"[*] 접속 대상 Qdrant DB: {QDRANT_URL}")
print(f"[*] 타겟 컬렉션: {COLLECTION_NAME}")
print("\n[경고] 진행 시 모든 사진의 유사도, 인물, 풍경 AI 벡터 데이터가 영구 삭제됩니다.")
confirm = input("정말로 초기화하고 모든 사진을 처음부터 재분석하시겠습니까? (Y/N): ")

if confirm.lower() != 'y':
    print("초기화를 취소합니다.")
    exit(0)

# 1. Qdrant 컬렉션 삭제 명령 (모든 데이터 백지화)
print("\n[1단계] 기존 AI 데이터베이스 파괴 중...")
try:
    resp = requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", timeout=10)
    if resp.status_code in [200, 201, 202, 404]: # 404 is fine (already deleted)
        print(" -> ✅ 벡터 DB 무결성 파괴(초기화) 성공!")
    else:
        print(f" -> ❌ DB 삭제 실패: HTTP {resp.status_code} - {resp.text}")
        exit(1)
except Exception as e:
    print(f" -> ❌ Qdrant 서버 통신 실패: {e}")
    exit(1)

# 2. vector_indexer.py 즉시 가동 (자동화 연계)
print("\n[2단계] 전체 사진 0.0% 부터 AI 재분석(Re-index) 파이프라인 가동 준비 중...")
print("-> vector_indexer 엔진으로 제어권을 넘깁니다.\n")
os.system("python /app/vector_indexer.py")
