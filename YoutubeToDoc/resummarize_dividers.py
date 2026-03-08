import json
import sqlite3
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
from bs4 import BeautifulSoup

sys.path.append("/app")

def update_db_prompt():
    db_path = "/app/data/settings.db"
    if not os.path.exists(db_path):
        print(f"DB 파일({db_path})을 찾을 수 없습니다.")
        return None, None
        
    system_prompt = "You are a professional summarizer. Create a concise summary in Korean. Do NOT include the main title. 1. Start with a plain text introduction like '본 영상은...'. 2. Use small headings (### or ####) for organizing the content. 3. Include a '핵심 인사이트' section. 4. End with a single bold sentence as a one-line summary."
    user_prompt = "다음은 영상에 대한 정보입니다. 다음 규칙에 따라 마크다운 형식으로 새롭게 요약해주세요:\n- 메인 제목(# 또는 ##) 작성 금지\n- '본 영상은~' 으로 시작하는 간단한 소개 문단 작성\n- 소개 문단 직후에 구분선(---)을 필수로 추가\n- 작은 주제(### 또는 그 이하)로 내용 정리\n- '핵심 인사이트' 작성 (리스트 형태 권장)\n- 핵심 인사이트 작성 직후에 구분선(---)을 필수로 추가\n- 가장 마지막에 굵은 글씨(** **)로 핵심을 관통하는 한줄 요약 작성\n\n{text}"

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE prompts SET summary_system_prompt=?, summary_user_prompt_template=? WHERE id=1", 
              (system_prompt, user_prompt))
    conn.commit()
    conn.close()
    
    print("✅ DB 프롬프트 업데이트 완료")
    return system_prompt, user_prompt

def regenerate_html(task_id):
    try:
        req = urllib.request.Request(
            "http://localhost:5000/admin/regenerate-html",
            data=json.dumps({"password":"admin", "task_id":task_id}).encode('utf-8')
        )
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req)
        return True
    except Exception as e:
        print(f"HTML 재생성 실패 {task_id}: {e}")
        return False

def main():
    sys_p, usr_p = update_db_prompt()
    if not sys_p:
        return

    load_dotenv("/app/.env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY가 없습니다.")
        return

    client = genai.Client(api_key=api_key)
    
    tasks_file = "/app/data/task_status.json"
    if not os.path.exists(tasks_file):
        print("task_status.json 파일이 없습니다.")
        return

    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    processed = 0
    total_to_process = len([t for t in tasks.values() if t.get("status") == "completed"])
    
    for task_id, task in tasks.items():
        if task.get("status") == "completed":
            video_title = task.get("video_title", task_id)
            safe_title = task.get("safe_title")
            if not safe_title:
                continue
            
            # Extract previous content from summary HTML to speed up and keep reliability
            out_dir = Path("/app/output") / safe_title
            summary_html1 = out_dir / f"{safe_title}-summary.html"
            summary_html2 = out_dir / f"{video_title}-summary.html"
            
            html_path = summary_html1 if summary_html1.exists() else summary_html2
            all_text = ""
            
            if html_path.exists():
                try:
                    with open(html_path, "r", encoding="utf-8") as bf:
                        html_content = bf.read()
                    soup = BeautifulSoup(html_content, "html.parser")
                    cap = soup.find("div", class_="caption markdown-body")
                    if cap:
                        all_text = cap.get_text(separator=" ", strip=True)
                except Exception as e:
                    print(f"HTML 파싱 에러 {safe_title}: {e}")
            
            # If parsing summary failed, fallback to task summary result
            if not all_text.strip():
                all_text = task.get("result", {}).get("summary", "")
                
            if not all_text.strip():
                print(f"자막 텍스트를 파싱하지 못함 {safe_title}")
                continue

            print(f"[{processed+1}/{total_to_process}] 재요약 중: {video_title[:30]}...")
            
            user_content = usr_p.replace("{text}", all_text)
            
            try:
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite-preview",
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_p,
                    )
                )
                new_summary = response.text.strip()
                
                if "result" not in task:
                    task["result"] = {}
                task["result"]["summary"] = new_summary
                
                with open(tasks_file, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=2)
                
                regenerate_html(task_id)
                print(f"✅ 완료: {video_title[:30]}")
                
                processed += 1
                    
            except Exception as e:
                print(f"❌ 실패 [{task_id}]: {e}")

    print(f"모든 작업 완료. {processed}개 재요약됨.")

if __name__ == "__main__":
    main()
