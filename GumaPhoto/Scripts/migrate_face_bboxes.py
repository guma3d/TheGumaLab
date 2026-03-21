import os
import cv2
import numpy as np
from PIL import Image, ImageOps
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from insightface.app import FaceAnalysis
import warnings

# 경고 무시
warnings.filterwarnings("ignore")

# 설정
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

def migrate_bboxes():
    print("===========================================================")
    print(" [얼굴 좌표(BBox) 소급 적용 스크립트 - Unknown People 전용]")
    print("===========================================================")
    
    try:
        client = QdrantClient(QDRANT_URL)
        
        print("\n[*] Qdrant DB 전체 스캔 중 (데이터베이스 글로벌 무결성 작업)...")
        
        target_points = []
        next_page = None
        while True:
            scroll_result, next_page = client.scroll(
                collection_name=COLLECTION_NAME,
                offset=next_page,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            for point in scroll_result:
                if point.payload and "face_bbox" not in point.payload:
                    filepath = point.payload.get("filepath")
                    if filepath:
                        target_points.append((point.id, filepath))
            
            if next_page is None:
                break
                
        total_targets = len(target_points)
        print(f"  [+] 총 {total_targets}장의 패치가 필요한(좌표가 없는) 사진을 발견했습니다!")
        
        if total_targets == 0:
            print("  [+] 모든 데이터베이스가 이미 완벽한 상태입니다. 스크립트를 종료합니다.")
            return

        print("\n[*] InsightFace 딥러닝 엔진(buffalo_l) 로딩 중 (VRAM 점유)...")
        face_app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        face_app.prepare(ctx_id=0, det_size=(640, 640))
        print("  [+] 엔진 로딩 완료. 즉시 초고속 추출을 시작합니다.\n")

        success_count = 0
        error_count = 0
        
        for idx, (p_id, fpath) in enumerate(target_points, 1):
            try:
                # HEIC를 지원하기 위해 PIL로 불러온 뒤 NumPy(BGR) 전환
                try:
                    pil_img = Image.open(fpath)
                    pil_img = ImageOps.exif_transpose(pil_img).convert("RGB")
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as img_err:
                    print(f"  [!] 파일 읽기 실패 (건너뜀): {fpath} / 사유: {img_err}")
                    error_count += 1
                    continue
                    
                if img is None:
                    print(f"  [!] 파일 읽기 완전 실패 (건너뜀): {fpath}")
                    error_count += 1
                    continue
                    
                faces = face_app.get(img)
                if not faces:
                    # 인식 실패
                    error_count += 1
                    continue
                    
                # 가장 컸던 얼굴(가장 메인 얼굴) 기준으로 다시 파싱
                best_face = sorted(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)[0]
                box = best_face.bbox.astype(int)
                x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(img.shape[1], box[2]), min(img.shape[0], box[3])
                
                # Qdrant에 덧씌우기 (Patch)
                client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload={"face_bbox": [int(x1), int(y1), int(x2), int(y2)]},
                    points=[p_id]
                )
                
                success_count += 1
                if idx % 100 == 0:
                    print(f"   => 진행률: {idx}/{total_targets} 장 완료...")
                    
            except Exception as ex:
                error_count += 1
                print(f"  [!] 오류 발생 ({fpath}): {ex}")
                
        print("\n===========================================================")
        print(f" [마이그레이션 종료] 최종 완료: {success_count}장 / 실패: {error_count}장")
        print("===========================================================")

    except Exception as e:
        print(f"\n[치명적 오류] 마이그레이션 실패: {e}")

if __name__ == "__main__":
    migrate_bboxes()
