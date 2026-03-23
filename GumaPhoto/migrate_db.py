import sqlite3
import json
import os
from qdrant_client import QdrantClient

def migrate():
    print("🚀 Starting Rescue Migration: Qdrant -> SQLite...")
    
    # 1. 최신 상태 DB 경로 설정 (이전 파일 지우고 완전 백지에서 시작)
    db_path = '/app/data/organizer_state.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"[*] 기존 {db_path} 초기화 완료.")
        
    db = sqlite3.connect(db_path)
    cur = db.cursor()
    
    # 2. 가장 완벽한 최신 스키마(Metadata 컬럼 포함) 생성
    cur.execute('''
        CREATE TABLE IF NOT EXISTS vectorized_files (
            filepath TEXT PRIMARY KEY,
            status TEXT,
            face_count INTEGER DEFAULT 0,
            metadata TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()
    print("[*] 신규 SQLite 스키마(vectorized_files) 생성 완료.")
    
    # 3. Qdrant 접속 후 모든 Payload 추출
    qc = QdrantClient('http://qdrant:6333')
    coll = 'gumaphoto_hybrid_kr'
    
    offset = None
    total_migrated = 0
    
    print("[*] Qdrant에서 23,882개 데이터 스트리밍 다운로드 시작...")
    while True:
        batch, next_offset = qc.scroll(
            collection_name=coll,
            limit=2000,
            with_payload=True,
            with_vectors=False,
            offset=offset
        )
        
        for p in batch:
            payload = p.payload
            filepath = payload.get('filepath')
            if not filepath:
                continue
                
            face_count = payload.get('face_count', 0)
            meta_str = json.dumps(payload, ensure_ascii=False)
            
            cur.execute("""
                INSERT OR REPLACE INTO vectorized_files (filepath, status, face_count, metadata) 
                VALUES (?, ?, ?, ?)
            """, (filepath, 'DONE', face_count, meta_str))
            
            total_migrated += 1
            
        db.commit()
        print(f"  -> 복구 진행 중... ({total_migrated} 개 완료)")
        
        if next_offset is None:
            break
        offset = next_offset
        
    db.close()
    
    # 4. 혼동을 막기 위해 쓸모없어진 구 버전 SQLite 영구 삭제
    old_db = '/app/data/gumaphoto_main.db'
    if os.path.exists(old_db):
        os.remove(old_db)
        print(f"[*] 혼동 방지용 과거 유물 DB ({old_db}) 영구 폐기 완료.")
        
    print(f"\n✅ Migration Complete! 총 {total_migrated}개의 AI 분석 데이터가 1초의 GPU 소모 없이 완벽하게 복원(동기화)되었습니다!")

if __name__ == '__main__':
    migrate()
