import os
import sys
import subprocess
from datetime import datetime
import concurrent.futures
import uuid

try:
    import exifread
except ImportError:
    print("⏳ 필요 패키지(exifread) 자동 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "exifread"])
    import exifread

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

import logging
logging.getLogger("exifread").setLevel(logging.CRITICAL)

def get_exif_date_worker(filepath):
    dt = None
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
    except Exception:
        pass
        
    if not dt:
        try:
            # EXIF 정보마저 없다면 OS의 '최종 수정 파일 날짜'를 백업으로 꺼내옵니다.
            dt = datetime.fromtimestamp(os.path.getmtime(filepath))
        except Exception:
            dt = datetime.min
            
    return filepath, dt

def rename_folder(tpath):
    valid_exts = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.mp4', '.mov', '.m4v'}
    all_files = []
    
    if os.path.isdir(tpath):
        for root, _, fs in os.walk(tpath):
            for f in fs:
                if os.path.splitext(f)[1].lower() in valid_exts:
                    all_files.append(os.path.join(root, f))
    else:
        print(f"\n❌ [{os.path.basename(tpath)}] 이 항목은 폴더가 아닙니다. 제외합니다.")
        return
        
    if not all_files:
        print(f"\n❌ [{os.path.basename(tpath)}] 대상 사진이 비어있습니다.")
        return
        
    print(f"\n============================================================")
    print(f"📁 [진입] 네이밍 그룹 자동 정렬 구역: {os.path.basename(tpath)} (총 {len(all_files)}장)")
    print(f"============================================================")
    
    print(f"   ... ⏳ [1/3] 16코어 엔진 가동: 촬영일자(EXIF) 100% 전수조사 수집 중...")
    
    max_workers = min(16, os.cpu_count() * 2)
    file_dates = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for r in executor.map(get_exif_date_worker, all_files):
            file_dates.append(r)
            
    # [핵심 수정] 사진이 위치한 '직속 부모 폴더(Subfolder)' 별로 그룹핑하여 각각 0001번부터 번호를 따로 매깁니다!
    from collections import defaultdict
    group_by_dir = defaultdict(list)
    for filepath, dt in file_dates:
        parent_dir = os.path.dirname(filepath)
        group_by_dir[parent_dir].append((filepath, dt))

    total_renamed = 0
    total_skipped = 0

    print(f"   ... 🛡️ [2/3] 사진 증발 방어막 전개: 이름 충돌을 막기 위한 '메모리 대피소' 격리 진행 중...")
    
    # ------------------------------------------------------------------------------------------
    # 각각의 하위 개별 폴더(2005-01, 2005-02 등)를 독립된 네이밍 세계관으로 처리
    for parent_dir, items in group_by_dir.items():
        # 사진 바로 위에 있는 직속 폴더명을 접두사로 사용 (예: '2024-12')
        subfolder_name = os.path.basename(parent_dir)
        
        # 1. 해당 폴더 안에서 과거 -> 미래 순서로 오름차순 정렬
        items.sort(key=lambda x: x[1])
        
        # 2. 임시 대피(UUID 발급)로 윈도우 OS 덮어쓰기 에러 원천 차단
        temp_stage = []
        for filepath, dt in items:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.jpeg': ext = '.jpg'
            
            tmp_name = f"gmtmp_{uuid.uuid4().hex[:8]}{ext}"
            tmp_path = os.path.join(parent_dir, tmp_name)
            try:
                os.rename(filepath, tmp_path)
                temp_stage.append((tmp_path, dt, ext))
            except Exception:
                temp_stage.append((filepath, dt, ext))
                
        # 3. 0001번부터 번호표 찰칵!
        for idx, (filepath, dt, ext) in enumerate(temp_stage):
            seq_num = idx + 1
            new_name = f"{subfolder_name}_{seq_num:04d}{ext}"
            new_path = os.path.join(parent_dir, new_name)
            
            try:
                os.rename(filepath, new_path)
                total_renamed += 1
            except Exception as e:
                print(f"   [-] 에러 ({os.path.basename(filepath)}): {e}")
                total_skipped += 1
    # ------------------------------------------------------------------------------------------
                
    print(f"   => 🏆 [성공] 총 {len(group_by_dir)}개 하위 폴더 독립 리네이밍! ({total_renamed}장 완료, 실패 {total_skipped})")
    
def main():
    print("=" * 60)
    print("🔄 GumaPhoto 사진 파일명 일괄 대청소기 (Run AutoRenamer)")
    print("=" * 60)
    
    first_run = True
    while True:
        target_paths = []
        if first_run and len(sys.argv) > 1:
            target_paths = sys.argv[1:]
        else:
            raw_input = input("\n" + "=" * 50 + "\n🔥 시간순 정렬 및 '연도-월_0001' 일괄 네이밍을 수행할\n   과거 년도별 폴더(2005~) 들을 한꺼번에 마우스로 드래그 하세요!\n   (종료:'Q')\n> ").strip()
            if not raw_input or raw_input.upper() in ['Q', 'QUIT', 'EXIT']:
                print("\n👋 툴을 종료합니다. 수고하셨습니다!")
                break
            import shlex
            try:
                target_paths = [p.strip('"').strip("'") for p in shlex.split(raw_input, posix=False)]
            except:
                target_paths = [raw_input.strip('"').strip("'")]
                
        first_run = False
        if target_paths:
            for idx, root_path in enumerate(sorted(target_paths)):
                rename_folder(root_path)
                
            print(f"\n🎉 훌륭합니다. 투입하신 모든 폴더 구역에 대한 파일명 청소 작업이 완벽하게 끝났습니다!")

if __name__ == "__main__":
    main()
