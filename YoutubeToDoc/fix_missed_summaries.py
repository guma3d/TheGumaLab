import json
import sqlite3
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys

sys.path.append("/app")

def update_db_prompt():
    db_path = "/app/data/settings.db"
    system_prompt = "You are a professional summarizer. Create a concise summary in Korean. Do NOT include the main title. 1. Start with a plain text introduction like '본 영상은...'. 2. Use small headings (### or ####) for organizing the content. 3. Include a '핵심 인사이트' section. 4. End with a single bold sentence as a one-line summary."
    user_prompt = "다음은 영상에 대한 정보입니다. 다음 규칙에 따라 마크다운 형식으로 새롭게 요약해주세요:\n- 메인 제목(# 또는 ##) 작성 금지\n- '본 영상은~' 으로 시작하는 간단한 소개 문단 작성\n- 작은 주제(### 또는 그 이하)로 내용 정리\n- '핵심 인사이트' 작성 (리스트 형태 권장)\n- 가장 마지막에 굵은 글씨(** **)로 핵심을 관통하는 한줄 요약 작성\n\n{text}"
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
    load_dotenv("/app/.env")
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    tasks_file = "/app/data/task_status.json"
    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    for task_id, task in tasks.items():
        if task.get("status") == "completed":
            summary = task.get("result", {}).get("summary", "")
            if not summary:
                continue
                
            # `# ` 또는 `## ` 로 시작하거나 '본 영상은' 으로 시작하지 않으면 구형 포맷일 가능성이 높음
            if summary.strip().startswith("#") or "본 영상은" not in summary[:100]:
                print(f"구형 요약 발견: {task.get('video_title')}")
                print("재요약 진행 중...")
                
                user_content = usr_p.replace("{text}", summary)
                
                try:
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite-preview",
                        contents=user_content,
                        config=types.GenerateContentConfig(
                            system_instruction=sys_p,
                        )
                    )
                    new_summary = response.text.strip()
                    
                    task["result"]["summary"] = new_summary
                    
                    with open(tasks_file, "w", encoding="utf-8") as f:
                        json.dump(tasks, f, ensure_ascii=False, indent=2)
                    
                    regenerate_html(task_id)
                    print(f"✅ 완료: {task.get('video_title')}")
                except Exception as e:
                    print(f"❌ 실패: {e}")

if __name__ == "__main__":
    main()
