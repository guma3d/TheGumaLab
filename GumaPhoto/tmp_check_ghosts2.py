import os
import json
import urllib.request

def check_files():
    # 1. Get Qdrant count
    q_count = 0
    try:
        url = "http://localhost:6337/collections/gumaphoto_hybrid_kr/points/count"
        req = urllib.request.Request(url, data=b"{}", headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            q_count = result.get('result', {}).get('count', 0)
    except Exception as e:
        q_count = f"Error: {e}"
        
    # 2. Get physical count
    physical_count = 0
    target_dir = "D:/Pictures"
    
    for root, dirs, files in os.walk(target_dir):
        # Apply the blacklist from indexer
        blacklist = ['OriginalSource', 'junk_screenshots', 'b_cuts', 'test_images', '.git', 'uploads_raw', 'enrolled', 'test', 'unknown']
        dirs[:] = [d for d in dirs if d not in blacklist]
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.heif')):
                physical_count += 1
                
    # 3. Sample 5000 and count missing
    missing_count = 0
    total_sampled = 0
    try:
        url = "http://localhost:6337/collections/gumaphoto_hybrid_kr/points/scroll"
        data = json.dumps({"limit": 5000, "with_payload": ["filepath"], "with_vector": False}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            points = result.get('result', {}).get('points', [])
            total_sampled = len(points)
            for p in points:
                fp = p.get('payload', {}).get('filepath', '')
                local_fp = fp.replace("/app/data/organized", "D:/Pictures")
                if not os.path.exists(local_fp):
                    missing_count += 1
    except Exception as e:
        print(f"Sampling err: {e}")

    print(f"Total points in Qdrant DB: {q_count}")
    print(f"Total physical files on disk: {physical_count}")
    print(f"Ghost estimate from sample: {missing_count} ghosts out of {total_sampled} sampled")

check_files()
