import os, json, urllib.request
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("/app/.env")

def update_db_prompt():
    import sqlite3
    system_prompt = "You are a professional summarizer. Create a concise summary in Korean. Do NOT include the main title. 1. Start with a plain text introduction like '본 영상은...'. 2. Use small headings (### or ####) for organizing the content. 3. Include a '핵심 인사이트' section. 4. End with a single bold sentence as a one-line summary."
    user_prompt = "다음은 영상에 대한 정보입니다. 다음 규칙에 따라 마크다운 형식으로 새롭게 요약해주세요:\n- 메인 제목(# 또는 ##) 작성 금지\n- '본 영상은~' 으로 시작하는 간단한 소개 문단 작성\n- 작은 주제(### 또는 그 이하)로 내용 정리\n- '핵심 인사이트' 작성 (리스트 형태 권장)\n- 가장 마지막에 굵은 글씨(** **)로 핵심을 관통하는 한줄 요약 작성\n\n{text}"
    return system_prompt, user_prompt

def regenerate_html(task_id):
    req = urllib.request.Request("http://localhost:5000/admin/regenerate-html", data=json.dumps({"password":"admin", "task_id":task_id}).encode('utf-8'))
    req.add_header('Content-Type', 'application/json')
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print("HTML Regen error:", e)

sys_p, usr_p = update_db_prompt()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

with open("/app/data/task_status.json", "r", encoding="utf-8") as f: 
    tasks = json.load(f)

for tid, task in tasks.items():
    if task.get("status") == "completed":
        stitle = task.get("safe_title") or task.get("result", {}).get("title", tid)
        
        # summary.html 파일 찾기
        html_path1 = f"/app/output/{stitle}/{stitle}-summary.html"
        html_path2 = f"/app/output/{stitle}/{task.get('video_title')}-summary.html"
        html_path = html_path1 if os.path.exists(html_path1) else html_path2
        
        if not os.path.exists(html_path): 
            continue
            
        with open(html_path, "r", encoding="utf-8") as f: 
            soup = BeautifulSoup(f.read(), "html.parser")
            
        cap = soup.find("div", class_="caption markdown-body")
        if cap:
            old_summary = cap.get_text(separator=' ', strip=True)
            if old_summary.strip().startswith("#") or "본 영상은" not in old_summary[:50]:
                print(f"[{stitle}] 낡은 요약 발견됨. 재처리합니다...")
                user_content = usr_p.replace("{text}", old_summary)
                
                try:
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite-preview", 
                        contents=user_content, 
                        config=types.GenerateContentConfig(system_instruction=sys_p)
                    )
                    
                    if "result" not in task:
                        task["result"] = {}
                        
                    task["result"]["summary"] = response.text.strip()
                    
                    with open("/app/data/task_status.json", "w", encoding="utf-8") as f: 
                        json.dump(tasks, f, ensure_ascii=False, indent=2)
                        
                    regenerate_html(tid)
                    print(f"✅ [{stitle}] 재요약 및 HTML 생성 완료")
                except Exception as e:
                    print(f"❌ Gemini Error [{stitle}]: {e}")

print("스크립트 종료")
