import os
from datetime import datetime

organized_dir = "/app/data/organized"
latest_xmp = None
latest_time = 0

print("디스크에서 가장 최근에 생성/수정된 XMP 파일을 추적합니다...")

try:
    for root, _, files in os.walk(organized_dir):
        for f in files:
            if f.endswith(".xmp"):
                path = os.path.join(root, f)
                mtime = os.path.getmtime(path)
                if mtime > latest_time:
                    latest_time = mtime
                    latest_xmp = path

    if latest_xmp:
        print(f"✅ 찾아낸 최신 파일: {latest_xmp}")
        dt = datetime.fromtimestamp(latest_time)
        print(f"⏰ 타임스탬프: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n[내용]")
        print("-" * 40)
        with open(latest_xmp, "r", encoding="utf-8") as file:
            print(file.read())
        print("-" * 40)
    else:
        print("❌ 어떤 XMP 파일도 찾지 못했습니다.")
except Exception as e:
    print(f"에러 발생: {e}")
