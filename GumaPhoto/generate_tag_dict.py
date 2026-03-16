import os
import json
from qdrant_client import QdrantClient

# Docker 컨테이너 내부나 외부에서 Qdrant 주소를 유동적으로 가져옵니다.
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6337") 
COLLECTION_NAME = "gumaphoto_hybrid_kr"

def generate_tag_dictionary(output_path="data/available_tags.json", q_client=None):
    if not q_client:
        q_client = QdrantClient(url=QDRANT_URL)
        
    print(f"[*] 고속 태그 사전 생성을 위해 Qdrant 전체 스캔을 시작합니다...")
    
    locations_set = set()
    offset = None
    limit = 1000
    total_points = 0
    
    # Qdrant 페이지네이션(무한 스크롤) 방식으로 메모리 초과 없이 전체 데이터 탐색
    while True:
        res = q_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            offset=offset,
            with_payload=["location"],
            with_vectors=False
        )
        
        points, next_page_offset = res
        for point in points:
            loc = point.payload.get("location")
            if loc and loc != "Unknown Location":
                locations_set.add(loc)
        
        total_points += len(points)
        print(f"  - 스캔 진행중... (현재 {total_points}장 탐색 완료)")
        
        if next_page_offset is None:
            break
        offset = next_page_offset
        
    locations_list = list(locations_set)
    locations_list.sort()
    
    # 최종 사전 JSON 객체 생성
    tag_dict = {
        "locations": locations_list
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tag_dict, f, indent=4, ensure_ascii=False)
        
    print(f"✅ 태그 사전 구축 완료! (총 {total_points}장 중 고유 장소 {len(locations_list)}개 발견)")
    print(f"💾 사전 파일 저장 위치 -> {output_path}")

if __name__ == "__main__":
    generate_tag_dictionary()
