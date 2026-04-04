import sqlite3
import json
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

# Get the exact unicode path
cursor.execute("SELECT filepath, metadata FROM vectorized_files")

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

count = 0
for filepath, meta_str in cursor.fetchall():
    if "2017-03_위치정보없음" in filepath:
        local_path = filepath.replace('/app/data/organized', 'D:/Pictures')
        print(f"Local Path: {local_path}")
        exif = get_exif_data(local_path)
        
        if "GPSInfo" in exif:
            print("  -> GPSInfo found:", exif["GPSInfo"])
        else:
            print("  -> No GPSInfo found in physical file!")
            
        count += 1
        if count >= 5:
            break
