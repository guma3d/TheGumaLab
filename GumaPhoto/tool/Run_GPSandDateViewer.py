import os
import sys

try:
    import exifread
except ImportError:
    import subprocess
    print("⏳ 'exifread' 패키지 자동 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "exifread"])
    import exifread

import logging
logging.getLogger("exifread").setLevel(logging.CRITICAL)

# 윈도우 특유의 폴더 잠김 현상(드래그 시 CWD 종속) 차단
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

def analyze_metadata(filepath):
    has_gps = False
    has_date = False
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        # Check GPS
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            has_gps = True
            
        # Check Date
        if 'EXIF DateTimeOriginal' in tags or 'EXIF CreateDate' in tags or 'Image DateTime' in tags:
            has_date = True
    except Exception:
        pass
    
    return has_gps, has_date

def main():
    print("=" * 60)
    print("📋 GumaPhoto GPS & Date 메타데이터 무결성 검사기 (Viewer)")
    print("=" * 60)
    
    target_paths = []
    if len(sys.argv) > 1:
        target_paths = sys.argv[1:]
    else:
        raw_input = input("\n메타데이터 결손(유실) 통계를 검사할 사진이나 폴더를 드래그 하세요:\n> ").strip()
        import shlex
        try:
            target_paths = [p.strip('"').strip("'") for p in shlex.split(raw_input, posix=False)]
        except Exception:
            target_paths = [raw_input.strip('"').strip("'")]
            
    valid_exts = {'.jpg', '.jpeg', '.png', '.heic', '.webp'}
    all_files = []
    
    for tpath in target_paths:
        if os.path.isfile(tpath):
            if os.path.splitext(tpath)[1].lower() in valid_exts:
                all_files.append(tpath)
        elif os.path.isdir(tpath):
            for root, _, fs in os.walk(tpath):
                for f in fs:
                    if os.path.splitext(f)[1].lower() in valid_exts:
                        all_files.append(os.path.join(root, f))
                        
    if not all_files:
        print("\n❌ 대상 파일(.jpg 등)을 찾을 수 없습니다.")
        input("엔터를 누르면 종료됩니다...")
        return
        
    print(f"\n🔍 총 {len(all_files)}장의 사진을 빛의 속도로 스캔합니다...\n")
    
    count_perfect = 0
    count_no_gps = 0
    count_no_date = 0
    count_no_both = 0
    
    for i, fpath in enumerate(all_files):
        has_gps, has_date = analyze_metadata(fpath)
        fname = os.path.basename(fpath)
        
        if not has_gps and not has_date:
            print(f"[{i+1}/{len(all_files)}] 🚨 {fname} : 위치(GPS) 없음, 촬영날짜 없음 (완전 깡통)")
            count_no_both += 1
        elif not has_gps:
            print(f"[{i+1}/{len(all_files)}] ⚠️ {fname} : 위치(GPS) 텅 비어있음")
            count_no_gps += 1
        elif not has_date:
            print(f"[{i+1}/{len(all_files)}] ⚠️ {fname} : 촬영일자(Date) 텅 비어있음")
            count_no_date += 1
        else:
            print(f"[{i+1}/{len(all_files)}] ✅ {fname} : 정상 보유 (문제없음)")
            count_perfect += 1
            
    print("\n============================================================")
    print("📊 [메타데이터 결손 유무 최종 검사 리포트]")
    print("============================================================")
    print(f"  ▶ 전체 정밀 스캔된 파일 수 : {len(all_files)} 장")
    print(f"  ▶ 💎 완벽한 사진 (둘 다 보유) : {count_perfect} 장\n")
    
    total_missing_gps = count_no_gps + count_no_both
    total_missing_date = count_no_date + count_no_both
    
    print(f"  ▶ ❌ 위치(GPS) 유실/누락 상태인 사진   : {total_missing_gps} 장")
    print(f"  ▶ ❌ 촬영날짜(Date) 유실/누락 상태인 사진 : {total_missing_date} 장")
    print(f"  ▶ 🚨 두 개 모두 완전히 유실된 심각한 사진 : {count_no_both} 장")
    
    if total_missing_gps > 0 or total_missing_date > 0:
        print(f"\n   => 💡 결손된 항목들을 복구하시려면 각 항목에 맞는 Writer 툴을 가동하세요!")
        
    print("============================================================\n")
    
    input("프로그램을 종료하려면 엔터를 누르세요...")

if __name__ == "__main__":
    main()
