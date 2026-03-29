import os
import sys
import subprocess
import re

try:
    import exifread
except ImportError:
    print("⏳ 'exifread' 패키지 자동 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "exifread"])
    import exifread

import logging
logging.getLogger("exifread").setLevel(logging.CRITICAL)

LOCAL_EXIFTOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exiftool_engine", "exiftool.exe")

# 윈도우 드래그 앤 드롭 시 타겟 폴더가 Python의 실행 CWD로 붙잡혀 잠기는(File in Use) 현상을 완벽 방해하기 위해 강제 경로 이탈
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

def check_exiftool():
    if not os.path.exists(LOCAL_EXIFTOOL):
        print(f"❌ [치명적 오류] ExifTool 엔진 실행 파일이 설치되지 않았습니다.")
        print(f"   예상 경로: {LOCAL_EXIFTOOL}")
        print("   먼저 GPS 툴을 한 번 가동하여 엔진 세팅이 완료되었는지 확인해주세요.")
        input("\n엔터를 누르면 종료됩니다...")
        sys.exit(1)

def has_date_metadata(filepath):
    """ 사진에 이미 촬영일자(Date) 메타데이터가 존재하는지 확인하는 함수 """
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        # 셋 중 하나라도 박혀있으면 이미 날짜를 온존하게 보유한 파일로 간주 (방어막)
        if 'EXIF DateTimeOriginal' in tags or 'EXIF CreateDate' in tags or 'Image DateTime' in tags:
            return True
    except:
        pass
    return False

def write_exif_date_batch(filepaths, exif_date):
    success_count = 0
    failed_count = 0
    error_logs = []
    
    batch_size = 100
    for i in range(0, len(filepaths), batch_size):
        batch = filepaths[i:i+batch_size]
        
        # 인수를 윈도우 쉘이 아닌 메모리상 표준입력(STDIN) 파이프를 통해 순수 UTF-8로 전달하여 NFD 한글 깨짐을 무효화
        args = [
            "-m", "-overwrite_original",
            "-charset", "FileName=utf8",
            "-charset", "utf8",
            f"-DateTimeOriginal={exif_date}",
            f"-CreateDate={exif_date}",
            f"-ModifyDate={exif_date}"
        ]
        args.extend(batch)
        args_str = "\n".join(args)
        
        try:
            res = subprocess.run([LOCAL_EXIFTOOL, "-@", "-"], input=args_str.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 정확한 파싱을 위해 윈도우 터미널 인코딩(CP949)을 사용
            out_str = res.stdout.decode('cp949', errors='ignore')
            for line in out_str.split('\n'):
                line = line.strip()
                if "image files updated" in line:
                    try:
                        success_count += int(line.split()[0])
                    except: pass
                elif "files weren't updated" in line or "image files unchanged" in line:
                    try:
                        failed_count += int(line.split()[0])
                    except: pass

            # 치명적 내부 에러만 추출하여 리스트에 축적
            if res.stderr:
                err_msg = res.stderr.decode('cp949', errors='ignore').strip()
                if err_msg and "Error" in err_msg:
                    print(f"   [엔진 에러]: {err_msg[:200]}...")
                    error_logs.append(err_msg)

        except Exception as e:
            print(f"❌ 파이썬 내부 실행 에러: {e}")
            failed_count += len(batch)
            error_logs.append(f"Python Fatal Error: {e}")
            
    return success_count, failed_count, error_logs

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
        print("\n❌ 지정된 경로에서 수정 대상 사진 파일(.jpg, .heic 등)을 찾지 못했습니다.")
        return
        
    all_files = fix_extensions_automatically(all_files)
        
    print("\n🔍 정밀 스캔 중... (경고: 기존 촬영일자가 박힌 사진은 보호를 위해 자동 배제됩니다)")
    filepaths_to_inject = []
    skipped_count = 0
    total_scanned_files = len(all_files)
    
    for fpath in all_files:
        if has_date_metadata(fpath):
            skipped_count += 1
        else:
            filepaths_to_inject.append(fpath)
            
    if not filepaths_to_inject:
        print(f"\n🎉 투척하신 {total_scanned_files}장의 사진 전부에 이미 촬영 날짜(Date) 정보가 꽉꽉 박혀있습니다! (수정 불필요)")
        return
        
    print(f"✅ 타겟 확정 완료: 총 {total_scanned_files}장 중 날짜가 텅 빈 사진만 {len(filepaths_to_inject)}장 확인되었습니다.")
    if skipped_count > 0:
        print(f"   (보존 처리됨: 사진 내부에 원본 날짜가 살아있는 {skipped_count}장의 사진은 자동 제외되었습니다)")
    
    print("\n👉 즉시 각 사진이 속한 '폴더 이름'을 분석하여 지능형 일괄 주입을 시작합니다...")
    
    batches_by_date = {}
    failed_to_parse = []
    
    date_pattern = re.compile(r'^((?:19|20)\d{2})(?:[-_.\s]?(\d{1,2}))?(?:[-_.\s]?(\d{1,2}))?')

    for fpath in filepaths_to_inject:
        folder_name = os.path.basename(os.path.dirname(fpath))
        match = date_pattern.search(folder_name)
        
        if match:
            y = match.group(1)
            m = match.group(2) if match.group(2) else "01"
            d = match.group(3) if match.group(3) else "01"
            m = m.zfill(2)
            d = d.zfill(2)
            
            if 1 <= int(m) <= 12 and 1 <= int(d) <= 31:
                exif_date = f"{y}:{m}:{d} 12:00:00"
                if exif_date not in batches_by_date:
                    batches_by_date[exif_date] = []
                batches_by_date[exif_date].append(fpath)
            else:
                failed_to_parse.append(fpath)
        else:
            failed_to_parse.append(fpath)

    total_success = 0
    total_failed = 0
    all_error_logs = []
    
    if batches_by_date:
        print("\n" + "=" * 60)
        print("💾 [폴더명 기반 스마트 날짜 강제 주입 가동]")
        print("=" * 60)
        
        for exif_date, files_in_date in batches_by_date.items():
            print(f"▶ [{exif_date.split()[0].replace(':', '-')}] 날짜 패턴 폴더 감지 -> {len(files_in_date)}장에 각인 중...")
            s, f, errs = write_exif_date_batch(files_in_date, exif_date)
            total_success += s
            total_failed += f
            all_error_logs.extend(errs)
            
    if failed_to_parse:
        print("\n" + "=" * 60)
        print("⚠️ [경고] 폴더명에서 날짜를 추출할 수 없어 주입이 누락된 사진들")
        print("=" * 60)
        print(f"  ▶ 총 {len(failed_to_parse)} 장의 사진은 폴더 이름에 '연도숫자'가 없어서 패스되었습니다.")
        for f in failed_to_parse[:3]:
            parent_folder = os.path.basename(os.path.dirname(f))
            print(f"     - 실패한 폴더명: [{parent_folder}] \\ {os.path.basename(f)}")
        if len(failed_to_parse) > 3:
            print(f"     ... (외 {len(failed_to_parse)-3} 장 생략)")
            
    print("\n" + "=" * 60)
    print("📊 [최종 날짜(Date) 작업 통계 리포트]")
    print("=" * 60)
    print(f"  ▶ 전체 스캔된 타겟 파일 수: {total_scanned_files} 장")
    print(f"  ▶ ⏭️ 기존 촬영일자가 보존되어 안전하게 건너뛴 사진: {skipped_count} 장")
    print(f"  ▶ ✅ 성공적으로 새 날짜가 지능형 주입된 깡통 사진: {total_success} 장")
    
    if total_failed > 0:
        print(f"  ▶ ❌ 주입 실패(엔진 에러): {total_failed} 장")
        if all_error_logs:
            print("     [실패 상세 사유 (수백 장일 경우 최대 5개만 로깅)]:")
            # 중복 에러 메시지 제거 후 출력
            unique_errs = list(dict.fromkeys(all_error_logs))
            for err in unique_errs[:5]:
                print(f"      └ {err}")
                
    if failed_to_parse:
        print(f"  ▶ ❌ 폴더명 파싱 불가(실패): {len(failed_to_parse)} 장")
    print("============================================================\n")

def main():
    print("=" * 60)
    print("📅 GumaPhoto 메타데이터 촬영 날짜 강제 주입기 (Smart Date Injector)")
    print("=" * 60)
    
    check_exiftool()
    
    first_run = True
    while True:
        target_paths = []
        
        if first_run and len(sys.argv) > 1:
            target_paths = sys.argv[1:]
        else:
            raw_input = input("\n" + "-" * 50 + "\n날짜를 주입할 사진 폴더를 통째로 드래그 앤 드롭 하세요!\n(종료하려면 아무것도 드래그하지 않고 그냥 '엔터키'를 치거나 'Q'를 입력하세요!)\n> ").strip()
            
            if not raw_input or raw_input.upper() in ['Q', 'QUIT', 'EXIT']:
                print("\n👋 툴을 안전하게 종료합니다. 수고하셨습니다!")
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
