import sqlite3

DB_PATH = "/app/data/organizer_state.db"

def find_mismatch():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 1. vectorizer에는 있는데 organizer에는 없는 파일 찾기
        c.execute("""
            SELECT filepath FROM vectorized_files 
            WHERE status='DONE' AND filepath NOT IN (
                SELECT filepath FROM processed_files
            )
        """)
        mismatched_files = c.fetchall()
        
        print(f"[*] 딥러닝 봇(vectorized)에는 있지만 분류 봇(processed)에는 없는 파일 수: {len(mismatched_files)}")
        for i, row in enumerate(mismatched_files[:20]):
            print(f"  {i+1}: {row[0]}")
            
        # 2. organizer에는 있는데 vectorizer에는 없는 파일 찾기 (동영상 제외)
        c.execute("""
            SELECT filepath FROM processed_files 
            WHERE filepath NOT LIKE '%.mp4' 
            AND filepath NOT LIKE '%.mov'
            AND filepath NOT IN (
                SELECT filepath FROM vectorized_files WHERE status='DONE'
            )
        """)
        mismatched_files_2 = c.fetchall()
        
        print(f"\n[*] 분류 봇(processed)에는 있지만 딥러닝 봇(vectorized)에는 없는 파일 수: {len(mismatched_files_2)}")
        for i, row in enumerate(mismatched_files_2[:20]):
            print(f"  {i+1}: {row[0]}")

        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == '__main__':
    find_mismatch()
