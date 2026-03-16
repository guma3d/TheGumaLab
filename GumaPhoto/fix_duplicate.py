import sqlite3

def clean_duplicates():
    try:
        conn = sqlite3.connect('/app/data/organizer_state.db')
        cur = conn.cursor()
        
        # 'processed_files' 테이블에서 'IMG_2536.jpeg'가 포함된 경로 삭제
        cur.execute("DELETE FROM processed_files WHERE filepath LIKE '%IMG_2536.jpeg%'")
        deleted_processed = cur.rowcount
        
        # 'vectorized_files' 테이블에서 '2026'이 포함된 경로 삭제 (혹시 남아있다면)
        cur.execute("DELETE FROM vectorized_files WHERE filepath LIKE '%2026%'")
        deleted_vector = cur.rowcount
        
        conn.commit()
        print(f"Deleted {deleted_processed} rows from processed_files")
        print(f"Deleted {deleted_vector} rows from vectorized_files")
        
    except Exception as e:
        print(f"SQLite error: {e}")

if __name__ == '__main__':
    clean_duplicates()
