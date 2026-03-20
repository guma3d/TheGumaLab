import os, shutil

src_raw = r'D:\TheGumaLab\GumaPhoto\data\uploads_raw'
src_png = r'D:\TheGumaLab\GumaPhoto\data\FeedbackTest_Sample\01'
dst = r'D:\TheGumaLab\GumaPhoto\data\FeedbackTest_Sample\04'

jpgs = []
heics = []
pngs = []

for r, _, fs in os.walk(src_raw):
    for f in fs:
        if f.lower().endswith('.jpg') and len(jpgs) < 2:
            jpgs.append(os.path.join(r, f))
        elif f.lower().endswith('.heic') and len(heics) < 2:
            heics.append(os.path.join(r, f))

for r, _, fs in os.walk(src_png):
    for f in fs:
        if f.lower().endswith('.png') and len(pngs) < 2:
            pngs.append(os.path.join(r, f))

os.makedirs(dst, exist_ok=True)
for p in jpgs + heics + pngs:
    shutil.copy(p, dst)
    print(f"Copied {p} to {dst}")
