import os
import time

def check_today(dir_path):
    if not os.path.exists(dir_path): return
    now = time.time()
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            p = os.path.join(root, f)
            if now - os.path.getmtime(p) < 3600:  # within last hour
                print("RECENT:", p)

print("Checking junk_screenshots...")
check_today("/app/data/junk_screenshots")
print("Checking b_cuts...")
check_today("/app/data/b_cuts")
