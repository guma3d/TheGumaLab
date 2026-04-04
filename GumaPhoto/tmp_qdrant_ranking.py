import json
import urllib.request
import os
from collections import Counter

url = "http://localhost:6337/collections/gumaphoto_hybrid_kr/points/scroll"
headers = {"Content-Type": "application/json"}

# Filter for missing locations
filter_query = {
    "should": [
        {"key": "location", "match": {"text": "Unknown"}},
        {"key": "location", "match": {"text": "위치정보없음"}}
    ]
}

folder_counts = Counter()
offset = None

while True:
    data = {"filter": filter_query, "limit": 1000, "with_payload": ["filepath", "location"]}
    if offset is not None:
        data["offset"] = offset
        
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            points = result.get('result', {}).get('points', [])
            offset = result.get('result', {}).get('next_page_offset')
            
            for p in points:
                filepath = p.get("payload", {}).get("filepath", "")
                loc = p.get("payload", {}).get("location", "")
                
                # Check for explicit Unknown Location triggers
                if "Unknown" in loc or "위치정보없음" in loc:
                    ext = os.path.splitext(filepath)[1].lower()
                    if ext == ".webp":
                        continue
                    
                    norm_path = filepath.replace('\\', '/')
                    folder = os.path.basename(os.path.dirname(norm_path))
                    folder_counts[folder] += 1
                    
            if not offset:
                break
    except Exception as e:
        print(f"Error fetching from Qdrant: {e}")
        break

with open('d:/TheGumaLab/GumaPhoto/unknown_qdrant_rank.txt', 'w', encoding='utf-8') as f:
    f.write("Top folders with Unknown Locations in Qdrant (excluding .webp):\n")
    for folder, count in folder_counts.most_common(20):
        f.write(f"{folder}: {count}\n")
