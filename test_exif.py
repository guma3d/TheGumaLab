import subprocess
import json

filepath = "/app/data/organized/2017/2017-03_위치정보없음/2017-03_993.jpg"

print(">> Applying Location ...")
cmd = ["exiftool", "-XMP:Location=테스트-장소", "-m", "-overwrite_original", filepath]
subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print(">> Extracting ...")
res = subprocess.run(["exiftool", "-j", "-c", "%+.6f", "-DateTimeOriginal", "-Location", "-GPSLatitude", "-GPSLongitude", filepath], capture_output=True, text=True)
if res.returncode == 0 and res.stdout.strip():
    try:
        d = json.loads(res.stdout)[0]
        print(d)
    except Exception as e:
        print("JSON parse failed", e)
else:
    print("Empty or error:", res.stderr)
