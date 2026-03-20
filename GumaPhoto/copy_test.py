import os, shutil

src = r'D:\TheGumaLab\GumaPhoto\data'
dst = r'D:\TheGumaLab\GumaPhoto\data\FeedbackTest_Sample\04'

jpgs = []
heics = []

for r, _, fs in os.walk(src):
    for f in fs:
        p = os.path.join(r, f)
        if f.lower().endswith('.jpg') and len(jpgs) < 2:
            jpgs.append(p)
        elif f.lower().endswith('.jpeg') and len(jpgs) < 2:
            jpgs.append(p)
        elif f.lower().endswith('.heic') and len(heics) < 2:
            heics.append(p)

os.makedirs(dst, exist_ok=True)
for p in jpgs + heics:
    shutil.copy(p, dst)
    print(f"Copied {p} to {dst}")
