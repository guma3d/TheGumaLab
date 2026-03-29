import os
import sys
import shutil
from datetime import datetime

try:
    import exifread
except ImportError:
    print("⏳ 'exifread' 패키지 자동 설치 중...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "exifread"])
    import exifread

import logging
logging.getLogger("exifread").setLevel(logging.CRITICAL)

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

def get_exif_date_ym(filepath):
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
        for tag in ['EXIF DateTimeOriginal', 'EXIF CreateDate', 'Image DateTime']:
            if tag in tags:
                d_str = str(tags[tag]).strip()
                try:
                    dt = datetime.strptime(d_str, '%Y:%m:%d %H:%M:%S')
                    return f"{dt.year:04d}-{dt.month:02d}"
                except ValueError:
                    pass
    except Exception:
        pass
    return "UnknownDate"

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
                if ext not in ['.jpg', '.jpeg']:
                    new_f = os.path.splitext(f)[0] + '.jpg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                if ext != '.png':
                    new_f = os.path.splitext(f)[0] + '.png'
            elif len(header) >= 8 and header[4:8] == b'ftyp':
                if ext not in ['.heic', '.heif', '.mp4', '.mov', '.m4v']:
                    new_f = os.path.splitext(f)[0] + '.heic'
            elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':
                if ext != '.webp':
                    new_f = os.path.splitext(f)[0] + '.webp'
            
            if new_f != f:
                if not os.path.exists(new_f):
                    os.rename(f, new_f)
                    re_count += 1
                else:
                    new_f = f
                    
            fixed_paths.append(new_f)
        except Exception:
            fixed_paths.append(f)
            
    if re_count > 0:
        print(f"   => 🛠️ [자기 수리] 실제 포맷과 이름이 불일치하여 에러를 내던 파일 {re_count}개의 확장자를 강제 교정했습니다.")
        
    return fixed_paths

def process_targets(target_paths):
    valid_exts = {'.jpg', '.jpeg', '.png', '.heic', '.webp'}
    all_files = []
    
    # 드래그한 폴더의 "상위 디렉토리(바탕화면 등)"를 베이스로 설정합니다.
    # 즉, 던져넣은 박스 안이 아니라 박스 바깥(옆자리)에 직접 연월일 폴더들이 주루룩 생깁니다.
    base_dir = os.path.dirname(os.path.abspath(target_paths[0]))
        
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
        print("\n❌ 정리할 대상 사진 파일(.jpg, .heic 등)을 찾지 못했습니다.")
        return
        
    all_files = fix_extensions_automatically(all_files)
        
    print(f"\n🔍 총 {len(all_files)}장 사진의 내부 촬영 날짜를 초고속 분석 중입니다...")
    
    stats = {}
    
    for i, fpath in enumerate(all_files):
        ym_folder = get_exif_date_ym(fpath)
        
        target_dir = os.path.join(base_dir, ym_folder)
        os.makedirs(target_dir, exist_ok=True)
        
        fname = os.path.basename(fpath)
        target_path = os.path.join(target_dir, fname)
        
        if os.path.abspath(fpath) != os.path.abspath(target_path):
            if os.path.exists(target_path):
                base, ext = os.path.splitext(fname)
                counter = 1
                while os.path.exists(target_path):
                    target_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1
            try:
                shutil.move(fpath, target_path)
            except Exception as e:
                print(f"   [오류] 이동 실패: {fpath} -> {e}")
                continue
                
        if ym_folder not in stats:
            stats[ym_folder] = 0
        stats[ym_folder] += 1
        
    print("\n" + "=" * 60)
    print("📊 [스마트 자동 분류(Auto Organizer) 최종 리포트]")
    print("=" * 60)
    print(f"  ▶ 전체 검사 및 바깥(상위 폴더)으로 분리 배출된 사진 수 : {len(all_files)} 장\n")
    
    sorted_folders = sorted(stats.keys(), key=lambda x: "9999-99" if x == "UnknownDate" else x)
    
    for folder in sorted_folders:
        icon = "🗑️" if folder == "UnknownDate" else "📅"
        print(f"  ▶ {icon} [{folder}] 폴더를 바깥 공간에 신규 생성하여 : {stats[folder]}장 분리 저장함")
        
    print("============================================================\n")

def main():
    print("=" * 60)
    print("📁 GumaPhoto 스마트 연/월 자동 분류기 (Auto Folder Organizer)")
    print("=" * 60)
    
    first_run = True
    while True:
        target_paths = []
        
        if first_run and len(sys.argv) > 1:
            target_paths = sys.argv[1:]
        else:
            raw_input = input("\n" + "-" * 50 + "\n연-월(YYYY-MM) 단위로 방을 나눠 정리할 '폴더'를 통째로 창 안에 드래그 하세요!\n※ (폴더 안에 있던 사진들이 전부 빠져나와 그 폴더의 바깥쪽(나란히)으로 예쁘게 재배치됩니다)\n> ").strip()
            
            if not raw_input or raw_input.upper() in ['Q', 'QUIT', 'EXIT']:
                print("\n👋 정리 툴을 안전하게 종료합니다. 수고하셨습니다!")
                break
                
            import shlex
            try:
                target_paths = [p.strip('"').strip("'") for p in shlex.split(raw_input, posix=False)]
            except Exception:
                target_paths = [raw_input.strip('"').strip("'")]
        
        first_run = False
        
        if target_paths:
            process_targets(target_paths)

if __name__ == "__main__":
    main()
