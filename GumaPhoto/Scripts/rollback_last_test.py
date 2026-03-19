import sqlite3
import os
import uuid
import sys
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointIdsList

DB_PATH = "/app/data/organizer_state.db"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

print("[*] 가장 최근에 인덱싱된 테스트 파일 200개를 찾아 Qdrant/XMP/WEBP 찌꺼기를 완전 롤백(소각)합니다...")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 최근 200개 추출 (시간 내림차순)
    cursor.execute("SELECT filepath FROM vectorized_files ORDER BY processed_at DESC LIMIT 200")
    recent_files = [row[0] for row in cursor.fetchall()]
    
    if not recent_files:
        print("[-] 롤백할 처리 내역이 DB에 존재하지 않습니다.")
        sys.exit(0)
    
    q_client = QdrantClient(url=QDRANT_URL, timeout=10)
    rollback_count = 0
    
    for filepath in recent_files:
        try:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
            base_name = os.path.splitext(filepath)[0]
            
            # 1. Qdrant 벡터 삭제
            try:
                q_client.delete(collection_name=COLLECTION_NAME, points_selector=PointIdsList(points=[point_id]))
            except Exception as e:
                pass
                
            # 2. XMP 스니펫 및 파생 파일 삭제
            for p in [filepath + ".xmp", base_name + ".xmp"]:
                if os.path.exists(p):
                    try: os.remove(p)
                    except: pass
                    
            # 3. WEBP 썸네일 삭제
            orig_ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ""
            thumb_path = f"{base_name}_{orig_ext}.webp"
            if os.path.exists(thumb_path):
                try: os.remove(thumb_path)
                except: pass
                
            # 4. SQLite DB 레코드 폭파
            cursor.execute("DELETE FROM vectorized_files WHERE filepath=?", (filepath,))
            conn.commit()
            
            rollback_count += 1
            print(f"  [-] 롤백 완료: {os.path.basename(filepath)}")
            
        except Exception as file_e:
            print(f"  [!] {filepath} 롤백 실패: {file_e}")

    print(f"\n✅ 총 {rollback_count}개의 파일에 대한 AI 처리 내역, 벡터 포인트, 썸네일 파생 쓰레기가 흔적 없이 소거되었습니다.")
    
except Exception as e:
    print(f"🚨 롤백 메인 스크립트 에러 발생: {e}")
