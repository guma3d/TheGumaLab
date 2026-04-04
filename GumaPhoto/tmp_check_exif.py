import sqlite3
import json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

cursor.execute("SELECT filepath, metadata FROM vectorized_files WHERE filepath LIKE '%2017-03_위치정보없음%' LIMIT 5")

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
                    exif_data[decoded] = value
    except Exception as e:
        print(f"Error reading EXIF from {image_path}: {e}")
    return exif_data

for filepath, meta_str in cursor.fetchall():
    print(f"Filepath in DB: {filepath}")
    # Replace the container path with the local path
    local_path = filepath.replace('/app/data/organized', 'D:/Pictures')
    # Use backslashes for Windows path if needed, but Python handles forward slashes well
    
    print(f"Local Path: {local_path}")
    exif = get_exif_data(local_path)
    
    if "GPSInfo" in exif:
        print("  -> GPSInfo found:", exif["GPSInfo"])
    else:
        print("  -> No GPSInfo found in physical file!")
        
    meta = json.loads(meta_str)
    print("  -> DB Meta Location:", meta.get('location'))
    print("-" * 40)
