import os
import sys
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_DIR = "/app/data/organized"
EXCLUDES = ["Unknown-Year", "uploads_raw"]

def scan_folder(folder):
    cmd = [
        "exiftool", "-q", "-j", "-r", "-ext", "jpg", "-ext", "jpeg", "-ext", "png", 
        "-DateTimeOriginal", "-CreateDate", "-ModifyDate", folder
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if not res.stdout.strip():
            return 0, []
        
        data = json.loads(res.stdout)
        
        local_total = len(data)
        local_missing = []
        for file_info in data:
            filename = file_info.get("SourceFile", "Unknown")
            dt = file_info.get("DateTimeOriginal") or file_info.get("CreateDate") or file_info.get("ModifyDate")
            
            if not dt:
                local_missing.append(filename)
                
        return local_total, local_missing
    except Exception as e:
        print(f"Error scanning folder {folder}: {e}")
        return 0, []

def check_dates():
    dirs_to_scan = []
    try:
        for item in os.listdir(TARGET_DIR):
            if item in EXCLUDES:
                continue
            item_path = os.path.join(TARGET_DIR, item)
            if os.path.isdir(item_path):
                dirs_to_scan.append(item_path)
    except Exception as e:
        print(f"Error accessing {TARGET_DIR}: {e}")
        sys.exit(1)

    print(f"Scanning {len(dirs_to_scan)} target folders with 10 threads...")
    
    total_photos = 0
    missing_dates = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_folder = {executor.submit(scan_folder, folder): folder for folder in dirs_to_scan}
        for future in as_completed(future_to_folder):
            folder = future_to_folder[future]
            try:
                t_count, m_list = future.result()
                total_photos += t_count
                missing_dates.extend(m_list)
                print(f"  [+] Scanned {os.path.basename(folder)}: {t_count} photos, {len(m_list)} missing.")
            except Exception as exc:
                print(f"  [-] Folder {os.path.basename(folder)} generated an exception: {exc}")

    print("\n" + "="*50)
    print(" 📊 DATE METADATA VERIFICATION REPORT ")
    print("="*50)
    print(f"Total Photos Scanned : {total_photos}")
    print(f"Photos Missing Date  : {len(missing_dates)}")
    print(f"Percentage Missing   : {len(missing_dates)/total_photos*100:.2f}%" if total_photos > 0 else "N/A")
    print("-" * 50)
    
    folder_counts = {}
    for f in missing_dates:
        # Extract immediate parent folder
        folder_name = os.path.basename(os.path.dirname(f))
        folder_counts[folder_name] = folder_counts.get(folder_name, 0) + 1
        
    if folder_counts:
        print("📁 Missing dates breakdown by immediate folder:")
        for k, v in sorted(folder_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {k}: {v} photos")
            
    if missing_dates:
        print("\n📁 Sample of specific photos missing metadata (up to 20):")
        for f in missing_dates[:20]:
            print(f"   - {f}")

if __name__ == "__main__":
    check_dates()
