import os
import re
import subprocess
import shutil
import concurrent.futures

PROCESS_DIR = "/process"

def process_single_image(filepath, f, folder_name, date_pattern):
    try:
        # 1. 안전성 확보: 이미 DateTimeOriginal 데이터가 존재하는지 검사
        check_cmd = ["exiftool", "-DateTimeOriginal", "-s3", filepath]
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
        existing_date = result.stdout.strip()
        
        if existing_date:
            return "skipped", None

        # 2. 누락된 경우: '파일명'의 언더바(_) 앞부분까지만 순수 날짜로 파싱
        pure_date_string = f.split('_')[0]
        match = date_pattern.search(pure_date_string)
        if not match:
            # 파일명에서 실패 시, '상위 폴더명'의 언더바 파싱 시도
            pure_folder_date = folder_name.split('_')[0]
            match = date_pattern.search(pure_folder_date)
            
            if not match:
                return "failed", None
                
        yyyy = match.group(1)
        mm = match.group(2) if match.group(2) else "01" # 월이 누락된 경우 강제로 01월(1월) 배정
        dd = match.group(3) if match.group(3) else "01" # 일이 누락된 경우 강제로 01일(1일) 배정
        
        # ExifTool Format: YYYY:MM:DD 12:00:00
        exif_time = f"{yyyy}:{mm}:{dd} 12:00:00"
        
        # -overwrite_original 로 백업 생성을 막습니다.
        cmd = [
            "exiftool", "-m", "-overwrite_original",
            f"-DateTimeOriginal={exif_time}",
            f"-CreateDate={exif_time}",
            filepath
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "modified", exif_time
            
    except Exception as e:
        return "error", f"{f}: {e}"

def run_preprocessing():
    print("====================================================")
    print(" 🛠️ GumaPhoto AI 전처리 도구 (Docker Container 내부) ")
    print("====================================================")
    
    if not os.path.exists(PROCESS_DIR):
        print(f"❌ '{PROCESS_DIR}' 경로가 마운트되지 않았습니다.")
        return

    # 1. 모든 동영상 파일 삭제 (이미지만 남김)
    print("\n[1단계] 동영상 파일 검열 및 삭제")
    video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv']
    deleted_videos = 0
    
    for root, dirs, files in os.walk(PROCESS_DIR):
        if "Unknown-Year" in dirs: dirs.remove("Unknown-Year")
        if "uploads_raw" in dirs: dirs.remove("uploads_raw")
        
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in video_exts:
                filepath = os.path.join(root, f)
                try:
                    os.remove(filepath)
                    deleted_videos += 1
                    print(f"  🗑️ 삭제됨: {f}")
                except Exception as e:
                    print(f"  ❌ 삭제 실패: {f} ({e})")
                    
    print(f"✅ 총 {deleted_videos}개의 동영상 파일이 영구 삭제되었습니다.")

    # 2. 파일명 및 폴더명을 읽어 누락된 날짜 EXIF 주입 (조건부 안전 덮어쓰기)
    print("\n[2단계] 파일명 기반 EXIF 생성일자 지능형 주입 (초고속 멀티스레딩 엔진)")
    modified_images = 0
    skipped_images = 0
    failed_images = 0
    
    date_pattern = re.compile(r'((?:19|20)\d{2})(?:[-.]?(0[1-9]|1[0-2]))?(?:[-.]?(0[1-9]|[12]\d|3[01]))?')
    
    futures = []
    
    # 20개의 Worker를 활성화하여 동시다발적으로 I/O를 치우는 전략 (가속기 분산처리)
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        for root, dirs, files in os.walk(PROCESS_DIR):
            if "Unknown-Year" in dirs: dirs.remove("Unknown-Year")
            if "uploads_raw" in dirs: dirs.remove("uploads_raw")
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.heic']:
                    filepath = os.path.join(root, f)
                    folder_name = os.path.basename(root)
                    futures.append(executor.submit(process_single_image, filepath, f, folder_name, date_pattern))
                    
        total_scanned = 0
        total_files = len(futures)
        
        if total_files == 0:
            print("  대기 중인 사진이 없습니다.")
        else:
            for future in concurrent.futures.as_completed(futures):
                total_scanned += 1
                if total_scanned % 100 == 0 or total_scanned == total_files:
                    print(f"  ⚡ {total_scanned}/{total_files}장 렌더 스레드 병렬 검사/주입 완료... (진행도: {int(total_scanned/total_files*100)}%)")
                
                res_type, detail = future.result()
                if res_type == "skipped":
                    skipped_images += 1
                elif res_type == "modified":
                    modified_images += 1
                elif res_type == "failed":
                    failed_images += 1
                elif res_type == "error":
                    print(f"  ❌ EXIF 검사/주입 에러: {detail}")
                    failed_images += 1

    print(f"\n✅ [멀티스레드 주입 완료]: 총 {modified_images}장의 사진에 날짜 메타데이터 이식이 완료되었습니다!")
    print(f"   [패스 완료]: 기존 메타데이터가 존재하여 안전하게 넘긴 사진: {skipped_images}장")
    print(f"   [단서 없음]: 파일/폴더명에서 날짜를 유추할 수 없어 실패한 사진: {failed_images}장")
    print("\n🚀 모든 전처리 과정이 완료되었습니다. 이제 이 폴더의 내용물들을 uploads_raw 로 이동하세요.")

if __name__ == "__main__":
    run_preprocessing()
