import sqlite3
import time
import subprocess
import os
import sys

# 터미널 실행 위치와 무관하게 무조건 GumaPhoto 루트에서 동작하도록 설정
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(project_root, 'data', 'organizer_state.db')
processor_script = os.path.join(project_root, 'Scripts', 'feedback_processor_v2.py')

def init_db():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # 단일 통제소 장부 테이블 생성
    cur.execute('''
        CREATE TABLE IF NOT EXISTS feedback_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            fb_type TEXT NOT NULL,
            correct_value TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

def pop_task():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 락(Lock)을 피하기 위해 최우선 1개만 조회
    # SQLite ALTER COLUMN 추가 전후 하위 호환성을 위해 pragma table_info 등으로 동청 확인하지 않고 에러 핸들링
    try:
        cur.execute('''
            SELECT id, doc_id, fb_type, correct_value, target_points
            FROM feedback_tasks 
            WHERE status = 'PENDING' 
            ORDER BY created_at ASC LIMIT 1
        ''')
        row = cur.fetchone()
    except sqlite3.OperationalError:
        # target_points 가 없는 구형 테이블인 경우
        cur.execute('''
            SELECT id, doc_id, fb_type, correct_value 
            FROM feedback_tasks 
            WHERE status = 'PENDING' 
            ORDER BY created_at ASC LIMIT 1
        ''')
        row_raw = cur.fetchone()
        row = (*row_raw, '[]') if row_raw else None
        
    if row:
        task_id = row[0]
        # 가져오자마자 곧바로 진행 중(PROCESSING) 상태로 덮어쓰기 완료하여 다른 쓰레드 간섭 배제
        cur.execute("UPDATE feedback_tasks SET status = 'PROCESSING' WHERE id = ?", (task_id,))
        conn.commit()
    conn.close()
    
    return row

def mark_task(task_id, new_status):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE feedback_tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def run_daemon():
    print("🛡️ [Singleton] Feedback Daemon (단일 통제소) 가동 완료. 큐 감시를 시작합니다...")
    init_db()
    
    while True:
        try:
            task = pop_task()
            if task:
                task_id, doc_id, fb_type, correct_value, tp_json = task
                print(f"📥 [Queue] 새 작업 획득: Task {task_id} (타입: {fb_type}, ID: {doc_id}) -> {correct_value} (타겟 수동 지정 여부: {len(tp_json) > 5})")
                
                # feedback_processor_v2.py 동기 호출 명령 구성
                cmd = ["python", processor_script, "--type", fb_type, "--doc_id", doc_id, "--target_points", tp_json]
                if fb_type == "face":
                    cmd.extend(["--name", correct_value])
                else:
                    cmd.extend(["--loc", correct_value, "--date", ""]) # 날짜는 아직 UI에서 넘겨받지 않음
                
                # check=True 를 통해 자식 프로세스가 완벽히 다 끝날 때까지 여기서 철벽 방어 대기(Block)
                print(f"🚀 [Daemon] feedback_processor_v2.py 가동 시작")
                result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ [Daemon] Task {task_id} 완벽 성공!")
                    mark_task(task_id, 'DONE')
                else:
                    print(f"❌ [Daemon] Task {task_id} 프로세서에서 치명적 에러 반환:\n{result.stderr}")
                    mark_task(task_id, 'FAILED')
                    
            else:
                # 대기열에 일이 없으면 1.5초간 슬립 방어
                time.sleep(1.5)
                
        except Exception as e:
            print(f"⚠️ [Daemon Core] 치명적 통제소 오류: {e}")
            time.sleep(5) # 무한 루프 폭주 방지

if __name__ == "__main__":
    run_daemon()
