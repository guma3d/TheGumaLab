import sqlite3

try:
    conn = sqlite3.connect('/app/data/organizer_state.db')
    cur = conn.cursor()
    
    # 지금 진행중인 vector_indexer.py 가 8500장의 파일중 ERROR로 마킹된 과거 파일도
    # Florence-2(CPU)로 다시 돌리느라 시간을 다 쓰고 있습니다 (1장당 30초).
    # 따라서 방금 업로드된 '2026'년도 테스트 사진을 제외한 나머지 ERROR 파일들을 우선 DONE으로 바꿔줍니다.
    
    cur.execute("UPDATE vectorized_files SET status='DONE' WHERE status='ERROR' AND filepath NOT LIKE '%2026%'")
    rows_updated = cur.rowcount
    conn.commit()
    
    print(f"Update completed: {rows_updated} old error files bypassed.")
except Exception as e:
    print(f"Error: {e}")
