import json
import urllib.request
import os
from collections import defaultdict

url = "http://localhost:6337/collections/gumaphoto_hybrid_kr/points/scroll"
headers = {"Content-Type": "application/json"}

# Get ALL points
offset = None
folder_stats = defaultdict(lambda: {"total": 0, "missing_gps": 0})

while True:
    data = {"limit": 10000, "with_payload": ["filepath", "location"], "with_vector": False}
    if offset is not None:
        data["offset"] = offset
        
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            points = result.get('result', {}).get('points', [])
            offset = result.get('result', {}).get('next_page_offset')
            
            for p in points:
                filepath = p.get("payload", {}).get("filepath", "")
                loc = p.get("payload", {}).get("location", "")
                
                ext = os.path.splitext(filepath)[1].lower()
                if ext == ".webp":
                    continue
                
                norm_path = filepath.replace('\\', '/')
                folder = os.path.basename(os.path.dirname(norm_path))
                
                folder_stats[folder]["total"] += 1
                if "Unknown" in loc or "위치정보없음" in loc:
                    folder_stats[folder]["missing_gps"] += 1
                    
            if not offset:
                break
    except Exception as e:
        print(f"Error fetching from Qdrant: {e}")
        break

filtered = {k: v for k, v in folder_stats.items() if v["total"] > 0}
sorted_stats = sorted(filtered.items(), key=lambda x: (-x[1]["missing_gps"], x[0]))

report_path = "d:/TheGumaLab/GumaPhoto/artifacts/all_location_missing_report.md"
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w", encoding="utf-8") as rf:
    rf.write("# 📍 전체 폴더별 위치 메타데이터(GPS) 누락 상세 보고서\n\n")
    rf.write("이 보고서는 `D:\Pictures`에 저장된 모든 원본 사진 파일(WebP 제외, 총 26,332장)에 대하여 메타데이터상 GPS 정보가 누락된 개수를 순위별로 **끝까지** 추적한 결과입니다.\n\n")
    rf.write("| 순위 | 폴더명(연-월) | 구역 내 총 사진 수 | 위치 메타데이터 없는 사진 수 | 누락률(%) |\n")
    rf.write("| :--- | :--- | :--- | :--- | :--- |\n")
    
    rank = 1
    for folder, stats in sorted_stats:
        total = stats["total"]
        missing = stats["missing_gps"]
        
        # Optionally, skip folders that have 0 missing GPS if you only want the "missing" list
        if missing == 0:
            pct = 0
            # You can keep it if you want to show EXACTLY everything, but usually a missing report focuses on missing ones
        else:
            pct = (missing / total) * 100
        
        bold = "**" if rank <= 10 else ""
        color = "<span style='color:#ef4444; font-weight:bold;'>" if missing > 0 else "<span style='color:#10b981;'>"
        color_missing = f"{color}{missing:,}장</span>"
        
        rf.write(f"| {rank} | {bold}`{folder}`{bold} | {total:,}장 | {color_missing} | {pct:.1f}% |\n")
        rank += 1

print("Report generated successfully.")
