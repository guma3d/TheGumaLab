import os
import sys

# 프로젝트 루트(app)를 모듈 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from api.utils.metadata_parser import MetadataParser

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

def run_migration():
    print("🚀 [GumaPhoto] 메타데이터 대통합 마이그레이션(Geocoding)을 시작합니다...")
    
    try:
        client = QdrantClient(url=QDRANT_URL, timeout=60)
        # 컬렉션 상태 확인
        collection_info = client.get_collection(COLLECTION_NAME)
        total_count = collection_info.points_count
        print(f"[*] Qdrant 연결 성공. 총 {total_count}개의 데이터가 존재합니다. 스캔을 시작합니다...")
    except Exception as e:
        print(f"[-] Qdrant 접속 실패: {e}")
        return

    offset = None
    processed = 0
    updated = 0

    while True:
        records, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        for record in records:
            processed += 1
            percent = (processed / total_count) * 100 if total_count > 0 else 0
            # \r을 사용하여 콘솔 도배 없이 제자리에서 숫자가 올라가도록 초고속 디스플레이 연출
            print(f"\r  [⏳ 진행 상태] {processed} / {total_count} 스캔 중... ({percent:.1f}%)", end="", flush=True)
            
            payload = record.payload or {}
            
            # geo_point (위경도)가 이미 들어있는지 최우선 확인
            geo_point = payload.get("geo_point", {})
            lat = geo_point.get("lat")
            lon = geo_point.get("lon")
            filename = payload.get("filename", "Unknown file")
            
            # 구버전이나 geo_point가 누락되었을 경우를 대비한 보험
            if lat is None or lon is None:
                lat = payload.get("lat")
                lon = payload.get("lon")
                
            if lat is not None and lon is not None:
                # 1. 새 구조(국가-도-시-동)로 변환
                new_location_str = MetadataParser.parse_location(lat, lon)
                old_location_str = payload.get("location", "Unknown Location")
                
                # 완전히 다르다면 덮어쓰기!
                if new_location_str != old_location_str and "Unknown" not in new_location_str:
                    try:
                        client.set_payload(
                            collection_name=COLLECTION_NAME,
                            payload={"location": new_location_str},
                            points=[record.id]
                        )
                        updated += 1
                        print() # \r 과 줄바꿈 겹침 방지
                        print(f"  [🔄 위치 교체 완료] 📷 {filename}")
                        print(f"      - ❌ 기존: {old_location_str}")
                        print(f"      - ✅ 신규: {new_location_str}")
                    except Exception as e:
                        print(f"  [-] 페이로드 업데이트 실패: {e}")

        if offset is None:
            break

    print(f"\n✅ 마이그레이션 완료! 총 {processed}개 스캔, {updated}개의 장소 태그가 새 양식으로 교체되었습니다.")

    print("\n[*] Qdrant 페이로드 기반으로 available_tags.json을 강제 재생성합니다...")
    try:
        locs = set()
        dates_set = set()
        offset = None
        while True:
            r_records, offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                offset=offset,
                with_payload=["location", "date"],
                with_vectors=False
            )
            for r in r_records:
                p = r.payload or {}
                if p.get("location") and p.get("location") != "Unknown Location":
                    locs.add(p.get("location"))
                if p.get("date") and p.get("date") != "Unknown Date":
                    import re
                    m = re.match(r'^(19|20)\d{2}-\d{2}', p.get("date"))
                    if m: dates_set.add(m.group(0))
            if offset is None: break
        
        import json
        with open("/app/data/available_tags.json", "w", encoding="utf-8") as f:
            json.dump({"locations": list(locs), "dates": list(dates_set)}, f, ensure_ascii=False)
        print(f"  [+] 총 {len(locs)}개의 최신 4단 계층 장소 태그가 추출되어 저장되었습니다.")
        
        # NLP 캐시 초기화
        import urllib.request
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/clear_nlp_cache", method="POST")
            with urllib.request.urlopen(req, timeout=3) as resp:
                print("  [+] 검색엔진 NLP 메모리 캐시가 즉시 강제 초기화되었습니다.")
        except:
            print("  [-] 검색엔진 NLP 캐시 초기화 요청 실패 (앱이 꺼져있을 수 있습니다).")

    except Exception as e:
        print(f"  [-] 태그 재생성 실패: {e}")

if __name__ == "__main__":
    run_migration()
