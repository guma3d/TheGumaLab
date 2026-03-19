import os
import time

def check_organized():
    dir_path = "/app/data/organized"
    now = time.time()
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            p = os.path.join(root, f)
            if now - os.path.getmtime(p) < 3600 and not f.endswith(".xmp"):
                print("ORGANIZED TODAY:", p)

check_organized()
