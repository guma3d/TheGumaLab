import os
import sys
import subprocess
import json
import time
from datetime import datetime
import concurrent.futures

try:
    import exifread
    from PIL import Image
    import imagehash
except ImportError:
    print("⏳ 필요 패키지(exifread, Pillow, imagehash) 자동 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "exifread", "Pillow", "imagehash", "pillow_heif"])
    import exifread
    from PIL import Image
    import imagehash

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

import logging
logging.getLogger("exifread").setLevel(logging.CRITICAL)

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

LOCAL_EXIFTOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exiftool_engine", "exiftool.exe")
if not os.path.exists(LOCAL_EXIFTOOL):
    LOCAL_EXIFTOOL = "exiftool"

def get_decimal_from_dms(dms, ref):
    if len(dms) < 3: return 0.0
    degrees = float(dms[0].num) / float(dms[0].den)
    minutes = float(dms[1].num) / float(dms[1].den) / 60.0
    seconds = float(dms[2].num) / float(dms[2].den) / 3600.0
    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds
    return round(degrees + minutes + seconds, 6)

def get_exif_data_worker(filepath):
    dt = None; lat = None; lon = None; lat_ref = None; lon_ref = None
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        for tag in ['EXIF DateTimeOriginal', 'EXIF CreateDate', 'Image DateTime']:
            if tag in tags:
                d_str = str(tags[tag]).strip()
                try:
                    dt = datetime.strptime(d_str, '%Y:%m:%d %H:%M:%S')
                    break
                except ValueError:
                    pass
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            lat = get_decimal_from_dms(tags['GPS GPSLatitude'].values, str(tags.get('GPS GPSLatitudeRef', 'N')))
            lon = get_decimal_from_dms(tags['GPS GPSLongitude'].values, str(tags.get('GPS GPSLongitudeRef', 'E')))
            lat_ref = str(tags.get('GPS GPSLatitudeRef', 'N'))
            lon_ref = str(tags.get('GPS GPSLongitudeRef', 'E'))
    except Exception:
        pass
    return filepath, dt, lat, lon, lat_ref, lon_ref

def get_phash_worker(img_dict):
    try:
        with Image.open(img_dict['path']) as img:
            img.thumbnail((1024, 1024))
            img_dict['phash'] = imagehash.phash(img)
    except Exception:
        img_dict['phash'] = False
    return img_dict

def fix_extensions_automatically(filepaths):
    fixed_paths = []
    re_count = 0
    for f in filepaths:
        try:
            with open(f, 'rb') as file:
                header = file.read(12)
            ext = os.path.splitext(f)[1].lower()
            new_f = f
            if header.startswith(b'\xff\xd8\xff'):
                if ext not in ['.jpg', '.jpeg']: new_f = os.path.splitext(f)[0] + '.jpg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                if ext != '.png': new_f = os.path.splitext(f)[0] + '.png'
            elif len(header) >= 8 and header[4:8] == b'ftyp':
                if ext not in ['.heic', '.heif', '.mp4', '.mov', '.m4v']: new_f = os.path.splitext(f)[0] + '.heic'
            elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':
                if ext != '.webp': new_f = os.path.splitext(f)[0] + '.webp'
            if new_f != f:
                if not os.path.exists(new_f):
                    os.rename(f, new_f)
                    re_count += 1
                else: new_f = f
            fixed_paths.append(new_f)
        except Exception:
            fixed_paths.append(f)
    if re_count > 0:
        print(f"   => 🛠️ [자기 수리] 실제 확장자 불일치 파일 {re_count}개 자동 교정.")
    return fixed_paths

def write_gps_batch(filepaths, lat, lon, lat_ref, lon_ref):
    if not filepaths: return True, ""
    
    args = [LOCAL_EXIFTOOL, "-m", "-overwrite_original", "-charset", "FileName=utf8", "-charset", "utf8", f"-GPSLatitude={abs(lat)}", f"-GPSLatitudeRef={lat_ref}", f"-GPSLongitude={abs(lon)}", f"-GPSLongitudeRef={lon_ref}"]
    args.extend(filepaths)
    
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=120)
        if res.returncode == 0: return True, ""
        else: return False, f"⚠️ 에러: {res.stderr}\n{res.stdout}"
    except Exception as e:
        return False, str(e)

def process_single_target(tpath):
    valid_exts = {'.jpg', '.jpeg', '.png', '.heic', '.webp'}
    all_files = []
    
    if os.path.isfile(tpath):
        if os.path.splitext(tpath)[1].lower() in valid_exts:
            all_files.append(tpath)
    elif os.path.isdir(tpath):
        for root, _, fs in os.walk(tpath):
            for f in fs:
                if os.path.splitext(f)[1].lower() in valid_exts:
                    all_files.append(os.path.join(root, f))
                    
    if not all_files:
        print(f"\n❌ [{os.path.basename(tpath)}] 경로에 인식 가능한 사진이 없습니다.")
        return {"folder": os.path.basename(tpath), "target": 0, "success": 0, "fail": 0, "skip": "사진 없음"}
        
    print(f"\n============================================================")
    print(f"📁 [진입] 독립 탐색 구역: {os.path.basename(tpath)} (스캔 대상 {len(all_files)}장)")
    print(f"============================================================")
    
    all_files = fix_extensions_automatically(all_files)
        
    has_gps_list = []
    no_gps_list = []
    
    max_workers = min(16, os.cpu_count() * 2)
    s_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_exif_data_worker, f) for f in all_files]
        completed = 0
        total = len(futures)
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 100 == 0 or completed == total:
                print(f"   ... ⏳ 메타데이터 추출 중 [{completed} / {total}]")
                
            r = future.result()
            filepath, dt, lat, lon, lref, rref = r
            if lat is not None and lon is not None:
                has_gps_list.append({'path': filepath, 'dt': dt, 'lat': lat, 'lon': lon, 'lref': lref, 'rref': rref, 'phash': None})
            else:
                no_gps_list.append({'path': filepath, 'dt': dt, 'phash': None})
                
    exif_time = time.time() - s_time
                
    if not no_gps_list:
        print(f"\n✨ 이 폴더의 모든 사진에 이미 GPS 위치 정보가 살아 숨쉬고 있습니다! (수정할 내용 없음)")
        return {"folder": os.path.basename(tpath), "target": 0, "success": 0, "fail": 0, "skip": "완벽함(100% GPS 보유)"}
        
    print(f"  ▶ 기준 사진(GPS O) : {len(has_gps_list)} 장, 깡통 사진(GPS X) : {len(no_gps_list)} 장 (소요시간: {exif_time:.1f}초)")

    print(f"\n🧠 [GPS 복원] AI pHash 지문 연산 가속 엔진 가동")
    THRESHOLD = 22 
    
    c_time = time.time()
    day_map_has_gps = {}
    for src in has_gps_list:
        sdt = src['dt']
        if sdt:
            day_key = sdt.date()
            if day_key not in day_map_has_gps: day_map_has_gps[day_key] = []
            day_map_has_gps[day_key].append(src)
            
    valid_no_gps = [t for t in no_gps_list if t['dt']]
    valid_target_dates = {t['dt'].date() for t in valid_no_gps}
    
    filtered_has_gps = []
    for d, srcs in day_map_has_gps.items():
        if d in valid_target_dates:
            filtered_has_gps.extend(srcs)
            
    combined_list = valid_no_gps + filtered_has_gps
    if combined_list:
        print(f"  ▶ 🚀 연산에 필요한 총 {len(combined_list)}개 이미지 초고속 썸네일 해시 추출 중...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(get_phash_worker, img) for img in combined_list]
            completed = 0
            total = len(futures)
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                if completed % 100 == 0 or completed == total:
                    print(f"   ... ⏳ 이미지 지문(pHash) 복호화 중 [{completed} / {total}]")
                future.result()
    
    p_time = time.time() - c_time
    print(f"  ▶ ⚡ 지문 추출/배차 가속 연산 완료! (소요시간: {p_time:.1f}초)")
    
    matched_targets = []
    failed_to_match_list = []
    
    for target in no_gps_list:
        tdt = target['dt']
        if not tdt:
            failed_to_match_list.append(target)
            continue
            
        t_phash = target.get('phash')
        if not t_phash:
            failed_to_match_list.append(target)
            continue
            
        candidates = day_map_has_gps.get(tdt.date(), [])
        if not candidates:
            failed_to_match_list.append(target)
            continue
            
        best_match = None
        best_dist = float('inf')
        
        for cand in candidates:
            c_phash = cand.get('phash')
            if c_phash:
                dist = t_phash - c_phash
                if dist < best_dist:
                    best_dist = dist
                    best_match = cand
                    
        if best_match and best_dist <= THRESHOLD:
            matched_targets.append({
                'path': target['path'],
                'lat': best_match['lat'],
                'lon': best_match['lon'],
                'lref': best_match['lref'],
                'rref': best_match['rref']
            })
            print(f"   => 💡 매칭 성공! [{os.path.basename(target['path'])}] (오차율 {best_dist}) ⬅️ [{os.path.basename(best_match['path'])}]")
        else:
            failed_to_match_list.append(target)

    success_phash = 0
    if matched_targets:
        grouped = {}
        for m in matched_targets:
            key = (m['lat'], m['lon'], m['lref'], m['rref'])
            if key not in grouped: grouped[key] = []
            grouped[key].append(m['path'])
            
        print(f"\n🚀 총 {len(matched_targets)}개의 사진에 위치 데이터 초고속 동기화 각인을 시작합니다!")
        for (lat, lon, lref, rref), paths in grouped.items():
            ok, err = write_gps_batch(paths, lat, lon, lref, rref)
            if ok: success_phash += len(paths)
            
    print("\n" + "-" * 50)
    print(f"🏁 [{os.path.basename(tpath)}] 구역 통계: 타겟 {len(no_gps_list)} 중 {success_phash} 개 복원 (실패 {len(no_gps_list) - success_phash})")
    print("-" * 50 + "\n")
    
    return {
        "folder": os.path.basename(tpath),
        "target": len(no_gps_list),
        "success": success_phash,
        "fail": len(no_gps_list) - success_phash,
        "skip": ""
    }

def main():
    print("=" * 60)
    print("🌍 GumaPhoto 지능형 GPS 독립 구역 순차 동기화 머신 (Smart GPS Sync 4.0)")
    print("=" * 60)
    
    first_run = True
    while True:
        target_paths = []
        if first_run and len(sys.argv) > 1:
            target_paths = sys.argv[1:]
        else:
            raw_input = input("\n" + "=" * 50 + "\n🔥 다수의 연도별(폴더별) 경로를 한꺼번에 드래그 하세요!\n   (탐색 범위는 다른 폴더와 섞이지 않고 각 구역 내로 엄격히 제한됩니다.) \n   (종료:'Q')\n> ").strip()
            if not raw_input or raw_input.upper() in ['Q', 'QUIT', 'EXIT']:
                break
            import shlex
            try:
                target_paths = [p.strip('"').strip("'") for p in shlex.split(raw_input, posix=False)]
            except:
                target_paths = [raw_input.strip('"').strip("'")]
                
        first_run = False
        if target_paths:
            # 폴더명 순서대로 예쁘게 정렬하여 가장 오래된 년도(2005)부터 2026까지 차례대로 처리
            target_paths.sort()
            total_folders = len(target_paths)
            print(f"\n📦 총 {total_folders}개의 독립적인 구역(폴더/파일)이 감지되었습니다. 1번째부터 차례대로 스캔에 돌입합니다!")
            
            grand_summary = []
            
            for idx, root_path in enumerate(target_paths):
                print(f"\n\n▶ [전체 진도율: {idx+1} / {total_folders} 번째 구역 진입]")
                res = process_single_target(root_path)
                grand_summary.append(res)
                
            print(f"\n🎉 훌륭합니다! 총 {total_folders}개 구역에 대한 독립적인 GPS 동기화 작업이 최종적으로 모두 완료되었습니다.")
            
            print("\n" + "=" * 60)
            print("🏆 [전체 구역 처리 최종 결산 리포트]")
            print("=" * 60)
            t_target = 0
            t_succ = 0
            for r in grand_summary:
                f_name = r.get("folder", "Unknown")
                succ = r.get("success", 0)
                fail = r.get("fail", 0)
                sc = r.get("skip", "")
                
                t_target += r.get("target", 0)
                t_succ += succ
                
                if sc:
                    print(f"  ▶ 📂 {f_name:<16} | ➖ 건너뜀 ({sc})")
                else:
                    print(f"  ▶ 📂 {f_name:<16} | 🎯 성공: {succ:>4} / ❌ 실패: {fail:>4} (타겟 {r.get('target')}장)")
                    
            print("-" * 60)
            print(f"  🔥 최종 결론: 총 {t_target} 장의 GPS 깡통 사진 중, [{t_succ} 장]의 GPS를 완벽히 연쇄 복원해 냈습니다!")
            print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
