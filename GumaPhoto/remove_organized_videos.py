import os
import sqlite3

DB_PATH = "/app/data/organizer_state.db"
ORGANIZED_DIR = "/app/data/organized"
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv'}

def remove_videos():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
    except Exception as e:
        print(f"DB Error: {e}")
        conn = None

    deleted_count = 0
    # 1. 파일 시스템에서 영상 삭제
    for root, dirs, files in os.walk(ORGANIZED_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in VIDEO_EXTS:
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {filepath}: {e}")
                    
    # 2. DB (processed_files) 에서 영상 기록 삭제
    db_deleted = 0
    if conn:
        try:
            c.execute("SELECT filepath FROM processed_files")
            rows = c.fetchall()
            
            for row in rows:
                filepath = row[0]
                ext = os.path.splitext(filepath)[1].lower()
                if ext in VIDEO_EXTS:
                    c.execute("DELETE FROM processed_files WHERE filepath=?", (filepath,))
                    db_deleted += 1
                    
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error during delete: {e}")
    
    print(f"✅ 완료: {deleted_count}개의 동영상 파일을 디스크에서 영구 삭제했습니다.")
    print(f"✅ 완료: {db_deleted}개의 동영상 이동 기록을 DB에서 청소했습니다.")

if __name__ == '__main__':
    remove_videos()
