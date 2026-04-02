import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, IsEmptyCondition
from api.services.insightface_service import InsightFaceModule
import core.state

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

def main():
    print("==================================================")
    print("🚀 [GumaPhoto] 안면 Bounding Box 긴급 복구 엔진 가동")
    print("==================================================")
    
    try:
        client = QdrantClient(QDRANT_URL)
        # BBOX가 비어있고, "No People"이 아닌 사진들만 스캔
        total_count = client.count(
            collection_name="gumaphoto_hybrid_kr", 
        ).count
        print(f"[*] DB 전체 사진 수: {total_count}장")
        
        face_module = InsightFaceModule()
        print("[*] InsightFace (buffalo_l) 모델 GPU VRAM 로딩 완료!")
        
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return

    offset = None
    processed = 0
    updated = 0
    start_time = time.time()
    
    # 5초간 대기 후 본격 시작
    print("\n⚠️ 5초 뒤 BBOX 스캔/복구를 시작합니다... (취소: Ctrl+C)")
    time.sleep(5)
    
    while True:
        try:
            res, offset = client.scroll(
                collection_name="gumaphoto_hybrid_kr",
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            print(f"❌ Qdrant 스크롤 오류: {e}")
            break
            
        if not res:
            break
            
        points_to_update = []
        for p in res:
            processed += 1
            payload = p.payload or {}
            
            # 1. 이미 BBOX가 있거나
            if payload.get("face_bbox"):
                continue
            
            # 2. 사람이 없으면(= No People) 스킵
            people_list = payload.get("people", [])
            if "No People" in people_list:
                # No People이라도 빈 배열을 넣어둘지 여부. 현재는 그냥 None
                continue
                
            filepath = payload.get("filepath", "")
            if not os.path.exists(filepath):
                continue
                
            try:
                # 얼굴 모델 추론 수행 (약 0.05초~0.1초 소요)
                an = face_module.analyze_image(filepath)
                new_bbox = an.get("payload", {}).get("face_bbox")
                
                if new_bbox:
                    points_to_update.append((p.id, new_bbox))
            except Exception as e:
                pass
                
        # 배치 BBOX 업데이트 (Qdrant I/O 비용 최소화)
        if points_to_update:
            for pid, bbox in points_to_update:
                client.set_payload(
                    collection_name="gumaphoto_hybrid_kr",
                    payload={"face_bbox": bbox},
                    points=[pid]
                )
            updated += len(points_to_update)
            
        elapsed = time.time() - start_time
        speed = processed / elapsed if elapsed > 0 else 0
        rem_sec = (total_count - processed) / speed if speed > 0 else 0
        rem_min = int(rem_sec // 60)
        
        log_msg = f"⏳ [얼굴 BBOX 복구 중] 진행도: {processed}/{total_count} 장 ({processed/total_count*100:.1f}%) | 🎯 복구: {updated}장 | 남은시간: 약 {rem_min}분"
        print(log_msg)
        try:
            with open("/app/data/indexer_geo_log.txt", "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
        except Exception:
            pass
        
        if offset is None:
            break
            
    total_time = time.time() - start_time
    print(f"\n✅ [완료] 총 {updated}장의 사진에 Face BBOX가 성공적으로 물리 복구(이식) 되었습니다!")
    print(f"총 소요 시간: {total_time/60:.1f}분")

if __name__ == "__main__":
    main()
