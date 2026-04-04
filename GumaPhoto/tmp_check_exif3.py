import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image_path):
    exif_data = {}
    try:
        image = Image.open(image_path)
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = str(value)[:50] # truncated for brevity
    except Exception as e:
        pass
    return exif_data

local_dir = 'D:/Pictures/2017/2017-03'
files = os.listdir(local_dir)
count = 0
for f in files:
    if not f.endswith('.jpg'):
        continue
    filepath = os.path.join(local_dir, f)
    exif = get_exif_data(filepath)
    if "GPSInfo" in exif:
        print(f"File: {f} -> HAS GPS INFO! {list(exif['GPSInfo'].keys())}")
        count += 1
    if count >= 10:
        break

print(f"Total checked, found {count} with GPS")
