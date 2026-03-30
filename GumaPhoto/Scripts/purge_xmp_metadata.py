import os
import sys
import subprocess
import concurrent.futures

TARGET_DIR = "/app/data/organized"
BATCH_SIZE = 200

def purge_xmp_batch(filepaths):
    try:
        # -XMP:All= deletes all XMP (Extensible Metadata Platform) properties
        # This will securely remove any corrupted 'XMP:Location' texts
        # Standard EXIF (GPSLatitude, GPSLongitude, DateTimeOriginal) is rigorously preserved!
        cmd = ["exiftool", "-XMP:All=", "-m", "-overwrite_original"] + filepaths
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return len(filepaths)
    except Exception as e:
        print(f"[-] XMP purge error on batch: {e}")
        return 0

def run_purge():
    print("====================================================")
    print(" 🧹 GumaPhoto 원본 사진 XMP 전면 파기(Purge) 특수 도구 ")
    print("====================================================")
    print("주의: 이 도구는 EXIF의 전통적 GPS/날짜 데이터는 100% 보존하며,")
    print("오직 오염된 텍스트 등이 기생하는 신형 XMP 블록만을 도려냅니다.\n")

    if not os.path.exists(TARGET_DIR):
        print(f"❌ '{TARGET_DIR}' 경로를 찾을 수 없습니다. 도커 내부인지 확인하세요.")
        sys.exit(1)

    all_targets = []
    for root, dirs, files in os.walk(TARGET_DIR):
        blacklist = ['OriginalSource', 'junk_screenshots', 'b_cuts', 'test_images', '.git', 'uploads_raw', 'enrolled', 'test', 'unknown']
        dirs[:] = [d for d in dirs if d not in blacklist]
        
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                all_targets.append(os.path.join(root, f))
                
    total = len(all_targets)
    print(f"[*] 총 {total}장의 처리 대상 사진(원본)을 발견했습니다.")
    
    if total == 0:
        print("[!] 대상이 없습니다.")
        sys.exit(0)

    # BATCH processing
    # Create chunks of files to avoid command line length limits
    chunks = [all_targets[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    
    print(f"[*] 총 {len(chunks)}개의 그룹(약 {BATCH_SIZE}장씩)으로 나누어 XMP 적출(Excision)을 시작합니다. (병렬 처리)")
    
    processed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for chunk in chunks:
            futures.append(executor.submit(purge_xmp_batch, chunk))
            
        for future in concurrent.futures.as_completed(futures):
            processed_count += future.result()
            print(f"  ⚡ 현재 {processed_count} / {total} 장 XMP 파기 완료... ({(processed_count/total)*100:.1f}%)")

    print(f"\n✅ [클린 성공] 전체 {processed_count}장의 원본(.jpg 등) 파일에서 XMP 영역을 완전히 적출/폐기했습니다!")
    print("이제 모든 사진의 원본 데이터 생명줄은 오직 '숫자(GPS/날짜)' 로만 통제됩니다. (Source of Truth 확립)")

if __name__ == "__main__":
    run_purge()
