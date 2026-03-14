import os
import cv2
import numpy as np
import warnings

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from insightface.app import FaceAnalysis
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# 모델 준비
print("[*] InsightFace (buffalo_l) 모델을 로드하는 중입니다...")
app = FaceAnalysis(name='buffalo_l', root='/root/.insightface')
try:
    app.prepare(ctx_id=0, det_size=(640, 640))
except Exception:
    app.prepare(ctx_id=-1, det_size=(640, 640))
print("[*] 모델 준비 완료!")

# Qdrant 연결 (docker-compose 내부 이름: qdrant)
qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
print(f"[*] 벡터 DB (Qdrant)에 연결합니다: {qdrant_url}")
client = QdrantClient(url=qdrant_url)

COLLECTION_NAME = "family_faces_test"

# 기존 컬렉션이 있다면 지우고 새로 깨끗하게 생성 (512차원, 코사인 유사도)
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=512, distance=Distance.COSINE),
)
print(f"[*] '{COLLECTION_NAME}' 컬렉션 (데이터 서랍) 세팅 완료!\n")

ENROLLED_DIR = "/app/data/enrolled"
TEST_DIR = "/app/data/test_images"

# ==========================================================
# 1단계: 가족 얼굴 등록 (Enrolment)
# ==========================================================
print("=== 📸 [1단계] 가족 단독 사진 학습(등록) 시작 ===")
point_id = 1
for person_name in os.listdir(ENROLLED_DIR):
    person_dir = os.path.join(ENROLLED_DIR, person_name)
    if not os.path.isdir(person_dir):
        continue
    
    for filename in os.listdir(person_dir):
        if filename.startswith('.'): 
            continue
            
        filepath = os.path.join(person_dir, filename)
        img = cv2.imread(filepath)
        if img is None:
            continue
        
        # 얼굴 스캔
        faces = app.get(img)
        if len(faces) == 0:
            print(f"[-] 🚫 {person_name}/{filename}: 얼굴을 찾지 못해 패스합니다.")
            continue
        
        # 여러 얼굴이 실수로 찍혀 있다면? (예: 뒤에 행인) -> '가장 얼굴 면적이 큰 사람'만 등록
        main_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
        
        # 512숫자 뭉치(벡터) Qdrant에 저장
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=main_face.embedding.tolist(),
                    payload={"name": person_name, "source_file": filename}
                )
            ]
        )
        print(f"[+] ✅ 등록 완료: '{person_name}' (파일: {filename}) -> {main_face.embedding.shape} 벡터 추출")
        point_id += 1

# ==========================================================
# 2단계: 랜덤 사진 속 가족 찾기 (Matching)
# ==========================================================
print("\n=== 🔍 [2단계] 테스트 사진 속 가족 찾기 분석 ===")
# 코사인 유사도 기준 (1.0 = 완벽 일치 일치, 보통 0.45 이상이면 동일인. InsightFace는 0.4~0.5가 적당합니다)
THRESHOLD = 0.45 

for filename in os.listdir(TEST_DIR):
    if filename.startswith('.'): 
        continue
    filepath = os.path.join(TEST_DIR, filename)
    
    img = cv2.imread(filepath)
    if img is None:
        continue
    
    faces = app.get(img)
    print(f"\n🖼️ 사진 분석: [{filename}] -> 총 {len(faces)}명의 얼굴 발견")
    
    for i, face in enumerate(faces):
        bbox = face.bbox.astype(int)
        area = f"x:{bbox[0]}~{bbox[2]}, y:{bbox[1]}~{bbox[3]}"
        
        # 방금 찾은 얼굴(512개 숫자)이랑 가장 비슷한 사람(상위 1명)을 Qdrant에서 검색 (최신 qdrant-client 문법 적용)
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=face.embedding.tolist(),
            limit=1
        )
        search_result = response.points
        
        if len(search_result) > 0:
            best_match = search_result[0] # 가장 비슷한 1명
            match_score = best_match.score # 0 ~ 1 사이의 유사도
            match_name = best_match.payload.get("name")
            
            if match_score >= THRESHOLD:
                # 우리 가족 식별!
                print(f"  👉 얼굴 {i+1}: 🎯 '{match_name}' 입니다! (유사도 점수: {match_score:.4f})  [영역: {area}]")
            else:
                # 비슷한 사람이 있긴 하지만 점수가 낮음 -> 낯선 사람
                print(f"  👉 얼굴 {i+1}: 👤 낯선 얼굴 (가장 비슷한 가족 '{match_name}' 와의 유사도: {match_score:.4f} -> 기준미달)")
        else:
            print(f"  👉 얼굴 {i+1}: 👤 낯선 얼굴 (비교할 DB 없음)")

print("\n[*] 모든 매칭 테스트가 완료되었습니다!")
