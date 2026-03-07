import urllib.request
import json
import re

BASE_URL = "http://localhost:8083"

def get_tasks():
    req = urllib.request.Request(f"{BASE_URL}/tasks")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8')).get('tasks', [])
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []

def get_html(task_id, view_type="summary"):
    try:
        req = urllib.request.Request(f"{BASE_URL}/view/{task_id}/{view_type}")
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return ""

def delete_task(task_id):
    req = urllib.request.Request(f"{BASE_URL}/delete/{task_id}", method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('success', False)
    except Exception as e:
        print(f"Error deleting task {task_id}: {e}")
        return False

def has_korean(text):
    return bool(re.search(r'[가-힣]', text))

def main():
    print("불량 문서 조사 시작...")
    tasks = get_tasks()
    deleted_count = 0
    
    for task in tasks:
        task_id = task['task_id']
        video_title = task.get('video_title', task_id)
        status = task.get('status')
        
        if status == 'completed':
            summary_html = get_html(task_id, "summary")
            is_bad = False
            
            # API 키 만료, 유효하지 않은 인자, 내부 서버 에러 등
            if "API key expired" in summary_html or "INVALID_ARGUMENT" in summary_html or "INTERNAL" in summary_html:
                is_bad = True
                
            if not summary_html or len(summary_html) < 200:
                is_bad = True
            
            # 한글 번역이 아예 없는지 검사 (마크다운 캡션 섹션에서)
            if not is_bad:
                # div class="caption markdown-body" 안의 텍스트가 영어만 있는지 (한글 없음) 확인
                match = re.search(r'<div class="caption markdown-body">(.*?)</div>', summary_html, re.DOTALL)
                if match:
                    body = match.group(1)
                    text_only = re.sub(r'<[^>]+>', '', body)
                    # 특수문자나 숫자 제외하고 길이가 10 이상인데 한글이 없다면 불량
                    if len(re.sub(r'[\d\s\W_a-zA-Z]', '', text_only)) == 0 and len(text_only) > 50:
                        is_bad = True

            if is_bad:
                print(f"[{video_title}] 문서를 삭제합니다... (번역/에러)")
                if delete_task(task_id):
                    deleted_count += 1
                else:
                    print(f"삭제 실패: {task_id}")
                    
        elif status in ('failed', 'interrupted', 'cancelled'):
            # 실패한 상태의 문서들 완전히 제거
            print(f"[{video_title}] 실패/취소된 문서를 삭제합니다...")
            if delete_task(task_id):
                deleted_count += 1
                
    print(f"정산 완료! 총 {deleted_count}개의 불량 데이터가 정리되었습니다.")

if __name__ == '__main__':
    main()
