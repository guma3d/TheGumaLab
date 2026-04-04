import os
import exifread
from collections import defaultdict
import datetime

target_dir = "/app/data/organized"
blacklist = ['OriginalSource', 'junk_screenshots', 'b_cuts', 'test_images', '.git', 'uploads_raw', 'enrolled', 'test', 'unknown']

folder_stats = defaultdict(lambda: {"total": 0, "missing_gps": 0})

def check_gps(filepath):
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            if 'GPS GPSLatitude' in tags:
                return True
    except Exception:
        pass
    return False

for root, dirs, files in os.walk(target_dir):
    dirs[:] = [d for d in dirs if d not in blacklist]
    folder_name = os.path.basename(root)
    
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
            fp = os.path.join(root, f)
            folder_stats[folder_name]["total"] += 1
            if not check_gps(fp):
                folder_stats[folder_name]["missing_gps"] += 1

filtered = {k: v for k, v in folder_stats.items() if v["total"] > 0}
sorted_stats = sorted(filtered.items(), key=lambda x: (-x[1]["missing_gps"], x[0]))

print("Total Folders Processed:", len(sorted_stats))
for rank, (folder, stats) in enumerate(sorted_stats, 1):
    print(f"{rank}|{folder}|{stats['total']}|{stats['missing_gps']}")
