import os
import subprocess
import shutil

# =========================================================================
# 1. 04 폴더 환경 / Result 폴더 비우고 다시 세팅
# =========================================================================
TARGET_DIR = r"/app/data/FeedbackTest_Sample/04"
RESULT_DIR = os.path.join(TARGET_DIR, "Result")

# 기존 Result 내용 싹 비우기
if os.path.exists(RESULT_DIR):
    shutil.rmtree(RESULT_DIR)
os.makedirs(RESULT_DIR, exist_ok=True)

# 04 위치에 있는 EXIF가 완벽히 없는 순백의 깡통 파일들을 다시 복사
for f in os.listdir(TARGET_DIR):
    if os.path.isfile(os.path.join(TARGET_DIR, f)):
        shutil.copy(os.path.join(TARGET_DIR, f), RESULT_DIR)

TARGET_FILES = [os.path.join(RESULT_DIR, f) for f in os.listdir(RESULT_DIR) if os.path.isfile(os.path.join(RESULT_DIR, f))]

# =========================================================================
# 날짜(Date) 파이프라인 시뮬레이션 개시 (사용자력: 25년 3월 -> UI에서 2025-03 전달)
# =========================================================================
ui_input_date = "2025-03"
print(f"[*] 사용자 날짜 피드백 수신: '{ui_input_date}'")

# --- Step C: feedback_processor_v2.py (ExifTool 덮어쓰기) 시뮬레이션 ---
for fpath in TARGET_FILES:
    cmd = ["exiftool"]
    
    # DateTimeOriginal (YYYY:MM:DD HH:MM:SS) 포맷 변환 강제 로직 작동
    parts = ui_input_date.split("-")
    yyyy = parts[0]
    mm = parts[1] if len(parts) > 1 else "01"
    dd = parts[2] if len(parts) > 2 else "01"
    exif_time = f"{yyyy}:{mm}:{dd} 12:00:00"
    
    cmd.extend([f"-DateTimeOriginal={exif_time}"])
    cmd.extend(["-overwrite_original", fpath])
    
    print(f"   [+] ExifTool 날짜 Stamping ({exif_time}): {os.path.basename(fpath)}")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("\n[*] 날짜 시뮬레이션이 종료되었습니다. Result 폴더를 확인하세요.")
