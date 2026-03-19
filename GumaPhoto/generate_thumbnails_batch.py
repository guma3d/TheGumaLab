import os
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

def process_single_image(filepath):
    """단일 이미지의 WEBP 썸네일을 생성합니다."""
    try:
        # 확장자를 .webp로 변경 (원본 확장자 포함) -> e.g. .heic -> _heic.webp
        orig_ext = os.path.splitext(filepath)[1].lower().replace('.', '')
        thumb_path = os.path.splitext(filepath)[0] + f"_{orig_ext}.webp"
        
        # 이미 존재하면 패스 (빠른 스킵)
        if os.path.exists(thumb_path):
            return "SKIPPED"
            
        # 변환 작업
        with Image.open(filepath) as img:
            from PIL import ImageOps
            # EXIF 회전 정보를 반영하여 픽셀 자체를 물리적으로 회전시킴 (초기화)
            img = ImageOps.exif_transpose(img)
            
            img.thumbnail((300, 300))  # 가로 또는 세로 최대 300px
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(thumb_path, "WEBP", quality=75)
            
        return "GENERATED"
    except Exception as e:
        return f"ERROR: {e}"

def run_batch(target_dir, limit=None, workers=4):
    print(f"🚀 [썸네일 제조 공장] 백그라운드 변환기 가동 시작!")
    print(f"👉 타겟 디렉토리: {target_dir}")
    print(f"👉 사용 코어 수: {workers}개")
    if limit:
        print(f"⚠️ [테스트 모드] 최대 {limit}장의 사진만 생성합니다.")
        
    if not os.path.exists(target_dir):
        print(f"❌ 오류: 경로를 찾을 수 없습니다 ({target_dir})")
        print("도커 컨테이너 내부에서 실행 중인지 확인해주세요.")
        return

    # 1. 파일 목록 수집
    print("⏳ 파일 목록을 수집 중입니다...")
    target_files = []
    supported_exts = {'.heic', '.jpg', '.jpeg', '.png'}
    
    for root, dirs, files in os.walk(target_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in supported_exts:
                # webp가 이미 처리되었는지 체크하기 위해 추가할 수 있지만 
                # ProcessPool 안에서 각 워커가 판단하는게 메모리상 효율적입니다.
                full_path = os.path.join(root, f)
                target_files.append(full_path)

    print(f"🔎 총 {len(target_files)}장의 처리 대상 후보를 찾았습니다.")
    
    if limit:
        # 테스트를 위해 존재하지 않는 녀석들만 추려서 limit개 자름
        tasks_to_run = []
        for p in target_files:
            orig_ext = os.path.splitext(p)[1].lower().replace('.', '')
            if not os.path.exists(os.path.splitext(p)[0] + f"_{orig_ext}.webp"):
                tasks_to_run.append(p)
                if len(tasks_to_run) >= limit:
                    break
        target_files = tasks_to_run
        print(f"🔎 이 중 WEBP가 없어서 실제 작업할 타겟 {len(target_files)}장 세팅 완료.")

    # 2. 멀티코어 병렬 처리
    success_count = 0
    skipped_count = 0
    error_count = 0
    
    print("\n🔥 변환 공정 시작 (잠시만 기다려주세요)...\n" + "="*50)
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_path = {executor.submit(process_single_image, path): path for path in target_files}
        
        for idx, future in enumerate(as_completed(future_to_path)):
            path = future_to_path[future]
            try:
                res = future.result()
                if res == "SUCCESS":
                    success_count += 1
                elif res == "SKIPPED":
                    skipped_count += 1
                else:
                    error_count += 1
                    print(f"[!] {res} -> {path}")
                    
            except Exception as exc:
                print(f"[!] Fatal Error -> {path}: {exc}")
                error_count += 1
                
            # 진행률 표시
            if (idx + 1) % 50 == 0 or (idx + 1) == len(target_files):
                print(f"진행 상황: {idx + 1} / {len(target_files)} 완료... (생성:{success_count}, 스킵:{skipped_count}, 에러:{error_count})")

    print("="*50)
    print(f"🎉 작업 완료! (생성 {success_count}장 | 통과 {skipped_count}장 | 에러 {error_count}장)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GumaPhoto Retroactive Thumbnail Engine")
    parser.add_argument("--limit", type=int, help="테스트용으로 변환할 최대 개수를 정합니다.", default=None)
    parser.add_argument("--workers", type=int, help="병렬 프로세스 코어 수 (기본 4)", default=4)
    parser.add_argument("--path", type=str, help="원본 사진 경로 (기본 /app/data/organized)", default="/app/data/organized")
    
    args = parser.parse_args()
    
    # 윈도우 로컬 실행 대비용 안전장치
    target_path = args.path
    if target_path == "/app/data/organized" and not os.path.exists(target_path):
        if os.path.exists("D:/Pictures"):
            target_path = "D:/Pictures"
            
    run_batch(target_dir=target_path, limit=args.limit, workers=args.workers)
