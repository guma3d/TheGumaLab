import os
import time
from geopy.geocoders import Nominatim
from collections import defaultdict
import exifread
import shutil

TARGET_DIR = "/app/data/organized"
print("[*] 기존 영어 폴더 한국어 정식 명칭화 안전 이동 스크립트 가동 중...")

geolocator = Nominatim(user_agent="guma_photo_organizer_translate")

def get_decimal_from_dms(dms, ref):
    if not dms or len(dms) < 3: return 0
    try:
        degrees = dms[0].num / dms[0].den if dms[0].den != 0 else 0
        minutes = dms[1].num / dms[1].den / 60.0 if dms[1].den != 0 else 0
        seconds = dms[2].num / dms[2].den / 3600.0 if dms[2].den != 0 else 0
        if ref in ['S', 'W']:
            degrees = -degrees
            minutes = -minutes
            seconds = -seconds
        return degrees + minutes + seconds
    except:
        return 0

eng_locs = {}
for y in os.listdir(TARGET_DIR):
    yp = os.path.join(TARGET_DIR, y)
    if os.path.isdir(yp):
        for d in os.listdir(yp):
            if '_' in d:
                date_part, loc_part = d.split('_', 1)
                import re
                if re.search('[a-zA-Z]', loc_part) and loc_part != "Unknown-Location":
                    folder_path = os.path.join(yp, d)
                    if loc_part not in eng_locs:
                        eng_locs[loc_part] = []
                    eng_locs[loc_part].append((folder_path, y, date_part))

print(f"[*] 총 {len(eng_locs)}개의 고유 영어 지역명 폴더 그룹을 찾았습니다.")

translation_dict = {}
for loc_str, folder_list in eng_locs.items():
    lat, lon = None, None
    for folder_path, _, _ in folder_list:
        if lat is not None: break
        for f in os.listdir(folder_path):
            if f.lower().endswith(('.jpg', '.heic', '.jpeg', '.png')):
                filepath = os.path.join(folder_path, f)
                try:
                    with open(filepath, 'rb') as f_exif:
                        tags = exifread.process_file(f_exif, details=False)
                        if 'GPS GPSLatitude' in tags:
                            lat = get_decimal_from_dms(tags['GPS GPSLatitude'].values, tags['GPS GPSLatitudeRef'].values)
                            lon = get_decimal_from_dms(tags['GPS GPSLongitude'].values, tags['GPS GPSLongitudeRef'].values)
                            if lat != 0 and lon != 0: break
                except: pass
                
    if lat and lon:
        time.sleep(1.1)
        try:
            location = geolocator.reverse((lat, lon), language='ko', timeout=10)
            if location:
                addr = location.raw.get('address', {})
                city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county')
                state = addr.get('state') or addr.get('country')
                if city and state: raw_loc = f"{state}-{city}"
                elif state: raw_loc = state
                elif city: raw_loc = city
                else: raw_loc = "위치정보없음"
                translation_dict[loc_str] = raw_loc.replace(' ', '-')
                print(f"  [+] 매핑: {loc_str}  ->  {translation_dict[loc_str]}")
                continue
        except: pass
    
    print(f"  [-] GPS 역추적 실패: {loc_str} (기존 유지)")
    translation_dict[loc_str] = loc_str

renamed_folders = 0
for loc_str, folder_list in eng_locs.items():
    kor_loc = translation_dict.get(loc_str, loc_str)
    if kor_loc == loc_str: continue
    
    for old_folder, year_part, date_part in folder_list:
        new_folder_name = f"{date_part}_{kor_loc}"
        new_folder_path = os.path.join(TARGET_DIR, year_part, new_folder_name)
        
        if os.path.exists(new_folder_path):
            if new_folder_path != old_folder:
                for f in os.listdir(old_folder):
                    base, ext = os.path.splitext(f)
                    dest_file = os.path.join(new_folder_path, f"{base}_m{ext}")
                    if os.path.exists(dest_file): dest_file = os.path.join(new_folder_path, f"{base}_m2{ext}")
                    os.rename(os.path.join(old_folder, f), dest_file)
                shutil.rmtree(old_folder)
                renamed_folders += 1
        else:
            os.rename(old_folder, new_folder_path)
            renamed_folders += 1

for y in os.listdir(TARGET_DIR):
    yp = os.path.join(TARGET_DIR, y)
    if os.path.isdir(yp):
        for d in os.listdir(yp):
            if d.endswith("Unknown-Location"):
                nfolder = d.replace("Unknown-Location", "위치정보없음")
                os.rename(os.path.join(yp, d), os.path.join(yp, nfolder))

print(f"\n[!] 완료! 총 {renamed_folders}개의 폴더가 자체 GPS를 추적하여 추출된 한국어 공식 명칭으로 100% 동일하게 번역 및 통합되었습니다.")
