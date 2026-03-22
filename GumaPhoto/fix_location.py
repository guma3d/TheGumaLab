import os
import shutil
import glob
import subprocess

fix_count = 0
unknowns = glob.glob("/app/data/organized/*/*_위치정보없음/*.*") + glob.glob("/app/data/organized/*/*_Unknown-Location/*.*")
for f in unknowns:
    if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
        res = subprocess.run(["exiftool", "-j", "-GPSLatitude", f], capture_output=True, text=True)
        if '"GPSLatitude"' in res.stdout:
            print(f"Found misplaced file with valid GPS: {f}")
            dest = os.path.join("/app/data/uploads_raw", os.path.basename(f))
            shutil.move(f, dest)
            fix_count += 1
            
print(f"Total files pushed back to uploads_raw for GPS re-processing: {fix_count}")
