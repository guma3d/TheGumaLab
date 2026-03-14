import os
from PIL import Image
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# Configuration
RAW_DIR = "/app/data/uploads_raw"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

def run_multilingual_hybrid_test():
    print(f"[*] Qdrant 벡터 데이터베이스 연결: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL)
    
    # 1. 컬렉션 초기화 (512차원)
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=512, distance=Distance.COSINE),
    )
    
    # Payload(메타데이터) 빠른 검색을 위한 인덱스 생성 (Hybrid 지원용)
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="original_context",
        field_schema="text"
    )

    # 2. 다국어 지원 최신 CLIP 모델 로드 (한국어 포함 50+ 언어 지원)
    # clip-ViT-B-32-multilingual-v1 은 OpenAI CLIP을 기반으로 다국어 지식을 증류시킨 최고 가성비 모델
    print("[*] 🌍 다국어(한국어) 멀티모달 AI 모델 로드 중 (clip-ViT-B-32-multilingual-v1) ...")
    model = SentenceTransformer('clip-ViT-B-32-multilingual-v1')
    
    # 3. 간단한 샘플 데이터 구축
    # 테스트를 위해 임의의 3가지 컨텍스트를 가진 샘플 데이터를 생성 (실제 이미지 파일 없이 텍스트 인코딩으로 모의 테스트)
    # 실제로는 `Image.open(...)`을 통해 사진을 Vector로 변환해야 함
    
    print("[*] 📸 샘플 데이터 벡터화 및 Qdrant 저장 (Hybrid Payload 포함)...")
    sample_data = [
        {"id": 1, "desc_pixel": "A man wearing a military uniform standing outdoors", "context": "2005_성욱_군대"},
        {"id": 2, "desc_pixel": "A bride and groom smiling in a hall", "context": "가족_결혼사진"},
        {"id": 3, "desc_pixel": "Beautiful calm beach with blue sky", "context": "2019_Guam_Trip"},
        {"id": 4, "desc_pixel": "People drinking coffee in a cafe", "context": "주말_일상"},
    ]
    
    points = []
    for item in sample_data:
        # 이 부분은 원래 img = Image.open(...) -> model.encode(img) 이지만, 시뮬레이션을 위해 영어 픽셀 묘사 텍스트를 인코딩함
        # 다국어 모델이므로 영어로 된 묘사를 벡터화해두면 한국어 쿼리로도 이 위치를 정확히 찾아냄
        simulated_img_emb = model.encode(item["desc_pixel"])
        
        points.append(PointStruct(
            id=item["id"],
            vector=simulated_img_emb.tolist(),
            payload={
                "original_context": item["context"], 
                "hidden_pixel_truth": item["desc_pixel"] # 시뮬레이션 확인용
            }
        ))
        
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print("[+] DB 저장 완료!\n")
    
    # 4. 한국어 + 하이브리드 검색 시뮬레이션
    queries = [
        "군복 입은 군인",  # 한국어 순수 벡터(Pixel) 검색
        "결혼식 사진",      # 한국어 순수 벡터(Pixel) 검색
        "맑은 날씨의 조용한 바다", # 한국어 순수 벡터(Pixel) 검색
    ]
    
    print("==================================================")
    print("🇰🇷 [한국어 자연어 검색] AI 모델 테스트 진행...")
    print("==================================================")
    
    for query in queries:
        query_emb = model.encode([query])[0]
        
        # 순수 벡터 검색 (픽셀 의미만으로 찾기)
        print(f"\n🔍 검색어: '{query}'")
        hits = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_emb.tolist(),
            limit=1
        ).points
        
        if hits:
            best = hits[0]
            print(f"  👉 [결과] 컨텍스트: '{best.payload['original_context']}' (픽셀: {best.payload['hidden_pixel_truth']})")
            print(f"  👉 [정확도 점수] {best.score:.3f}")

if __name__ == "__main__":
    run_multilingual_hybrid_test()
