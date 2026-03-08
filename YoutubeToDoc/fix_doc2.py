import os
import json
import re
from Server import generate_summary_html, TASK_STATUS_FILE
from pathlib import Path
from bs4 import BeautifulSoup

def fix_doc():
    target_title = "Building Open Worlds in Unreal Engine 5 | Unreal Fest 2022"
    with open(TASK_STATUS_FILE, 'r', encoding='utf-8') as f:
        task_status = json.load(f)
    
    for tid, t in task_status.items():
        if t.get('status') == 'completed':
            result_data = t.get('result', {})
            # Check original_title or current title
            title = result_data.get('title', tid)
            original_title = result_data.get('original_title', '')
            video_title = t.get('video_title', '')
            
            if target_title in title or target_title in original_title or target_title in video_title:
                print(f"[{tid}] Found matching document: {title}")
                
                summary_html_path = result_data.get('summary_html_path', '')
                if not summary_html_path or not os.path.exists(summary_html_path):
                    print("Summary HTML not found.")
                    continue
                
                with open(summary_html_path, 'r', encoding='utf-8') as sf:
                    content = sf.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                cap_div = soup.find('div', class_='caption')
                
                if cap_div:
                    raw_text = cap_div.decode_contents()
                    
                    tags = result_data.get('tags', [])
                    youtube_url = t.get('url', '')
                    display_title = original_title or title
                    output_path = Path(summary_html_path).parent
                    
                    # The Server.py generate_summary_html NOW holds both defense mechanics, so just parsing and passing text is enough
                    generate_summary_html(raw_text, output_path, title, youtube_url, display_title, tags)
                    
                    print(f"Successfully fixed and regenerated summary HTML for: {title}")
                else:
                    print("Could not extract original markdown text from caption div.")
                break
    else:
        print("Target document not found in task_status.json.")

if __name__ == '__main__':
    fix_doc()
