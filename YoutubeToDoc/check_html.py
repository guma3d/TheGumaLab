import urllib.request
import json
import sqlite3

def check_db():
    conn = sqlite3.connect('/app/data/settings.db')
    c = conn.cursor()
    c.execute("SELECT summary_user_prompt_template FROM prompts WHERE id=1")
    res = c.fetchone()
    if res:
        print("DB Prompt:", res[0])
    conn.close()

def check_json():
    with open('/app/data/task_status.json', 'r', encoding='utf-8') as f:
        tasks = json.load(f)
        for tid, t in tasks.items():
            if t.get("video_title") == "Cartoony Animation! UE5 GPU Deformers (Sculpt & Lattice)":
                print("\nJSON Summary:", t.get("result", {}).get("summary", "")[:300])
                break

if __name__ == "__main__":
    check_db()
    check_json()
