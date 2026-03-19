import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
dir_path = "D:/Pictures/2019/2019-12_Hagåtña-Guam"
print("Files in", dir_path)
for f in os.listdir(dir_path):
    if "2019-12_222" in f:
        print(" ->", f)
