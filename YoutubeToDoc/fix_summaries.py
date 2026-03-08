import os
import json
import re
from Server import generate_summary_html, TASK_STATUS_FILE
from pathlib import Path
from bs4 import BeautifulSoup

def regenerate_all_summaries():
    with open(TASK_STATUS_FILE, 'r', encoding='utf-8') as f:
        task_status = json.load(f)
    
    count = 0
    for tid, t in task_status.items():
        if t.get('status') == 'completed':
            result_data = t.get('result', {})
            title = result_data.get('title', tid)
            original_title = result_data.get('original_title', '')
            
            summary_html_path = result_data.get('summary_html_path', '')
            if not summary_html_path or not os.path.exists(summary_html_path):
                continue
            
            try:
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
                    
                    # Re-generate to include new HTML layout (Retry button + JS)
                    generate_summary_html(raw_text, output_path, title, youtube_url, display_title, tags)
                    print(f"[{tid}] Regenerated summary HTML for: {title}")
                    count += 1
            except Exception as e:
                print(f"Error processing {tid}: {e}")

    print(f"Successfully regenerated {count} summaries.")

if __name__ == '__main__':
    regenerate_all_summaries()
