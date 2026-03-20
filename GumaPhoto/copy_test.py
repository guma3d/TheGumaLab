import os, shutil

src = r'D:\Pictures'
dst = r'D:\TheGumaLab\GumaPhoto\data\FeedbackTest_Sample\04'

heics = []
mp4s = []

for r, _, fs in os.walk(src):
    for f in fs:
        p = os.path.join(r, f)
        if f.lower().endswith('.heic') and len(heics) < 2:
            heics.append(p)
        elif f.lower().endswith('.mp4') and len(mp4s) < 2:
            mp4s.append(p)
    if len(heics) >= 2 and len(mp4s) >= 2:
        break

os.makedirs(dst, exist_ok=True)
for p in heics + mp4s:
    shutil.copy(p, dst)
    print(f"Copied {p} to {dst}")
