import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from collections import defaultdict

def has_gps_info(image_path):
    try:
        with Image.open(image_path) as img:
            info = img._getexif()
            if info:
                for tag, value in info.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        return True
    except Exception:
        pass
    return False

def analyze_pictures(target_dir="D:/Pictures"):
    blacklist = ['OriginalSource', 'junk_screenshots', 'b_cuts', 'test_images', '.git', 'uploads_raw', 'enrolled', 'test', 'unknown']
    
    # folder => {"total": 0, "missing_gps": 0}
    folder_stats = defaultdict(lambda: {"total": 0, "missing_gps": 0})
    
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in blacklist]
        folder_name = os.path.basename(root)
        
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                filepath = os.path.join(root, f)
                folder_stats[folder_name]["total"] += 1
                
                # Check for GPS metadata
                if not has_gps_info(filepath):
                    folder_stats[folder_name]["missing_gps"] += 1

    # Filter out folders with 0 photos just in case
    filtered_stats = {k: v for k, v in folder_stats.items() if v["total"] > 0}
    
    # Sort by number of missing GPS (descending), then alphabetically by folder
    sorted_stats = sorted(filtered_stats.items(), key=lambda x: (-x[1]["missing_gps"], x[0]))
    
    # Write report to markdown file to be used as artifact
    report_path = "d:/TheGumaLab/GumaPhoto/artifacts/gps_missing_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# 📍 폴더별 위치 메타데이터(GPS) 누락 상세 보고서\n\n")
        rf.write("이 보고서는 `D:\Pictures`의 모든 이미지 파일(WebP 제외)의 **물리적 EXIF 메타데이터**를 전수 조사하여, 폴더별로 GPS 정보가 없는 사진의 개수를 순서대로 정리한 것입니다.\n\n")
        rf.write("| 순위 | 폴더명(연-월) | 총 사진 수 | 위치정보 없는 사진 수 | 누락률(%) |\n")
        rf.write("| :--- | :--- | :--- | :--- | :--- |\n")
        
        for rank, (folder, stats) in enumerate(sorted_stats, 1):
            total = stats["total"]
            missing = stats["missing_gps"]
            if missing == 0:
                continue # Skip folders where all photos have GPS
            pct = (missing / total) * 100 if total > 0 else 0
            
            bold = "**" if rank <= 10 else ""
            rf.write(f"| {rank} | {bold}`{folder}`{bold} | {total:,}장 | <span style='color:#ef4444; font-weight:bold;'>{missing:,}장</span> | {pct:.1f}% |\n")

    print(f"Analysis complete. Found {len(sorted_stats)} folders. Report saved.")

analyze_pictures()
