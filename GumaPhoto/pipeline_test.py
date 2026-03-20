import os
import json
import subprocess
import shutil
from geopy.geocoders import Nominatim
import google.generativeai as genai

# =========================================================================
# 1. 04 폴더 환경 / Result 폴더 기본 세팅 선언
# =========================================================================
TARGET_DIR = r"/app/data/FeedbackTest_Sample/04"
RESULT_DIR = os.path.join(TARGET_DIR, "Result")
os.makedirs(RESULT_DIR, exist_ok=True)

# 샘플 사진들을 Result 폴더로 복사 (안전띠)
for f in os.listdir(TARGET_DIR):
    if os.path.isfile(os.path.join(TARGET_DIR, f)):
        shutil.copy(os.path.join(TARGET_DIR, f), RESULT_DIR)

TARGET_FILES = [os.path.join(RESULT_DIR, f) for f in os.listdir(RESULT_DIR) if os.path.isfile(os.path.join(RESULT_DIR, f))]

# =========================================================================
# 파이프라인 시뮬레이션 개시
# =========================================================================
user_input = "푸꾸옥"
print(f"[*] 사용자 실제 입력: '{user_input}'")

# --- Step A: main.py 의 submit_feedback_v2 파싱 프로세스 시뮬레이션 ---
def simulate_gemini_parsing(input_str):
    existing_locations = []
    if os.path.exists("/app/data/available_tags.json"):
        with open("/app/data/available_tags.json", "r", encoding="utf-8") as f:
            tag_data = json.load(f)
            existing_locations = tag_data.get("locations", [])
            
    prompt = (
        f"사용자 입력 장소: '{input_str}'\n"
        "당신은 스마트 갤러리의 위치 정보 표준화 매니저입니다.\n"
        "사용자가 구어체나 부분 약어로 장소를 입력하더라도, 다음의 <보유 장소 목록> 중에서 가장 정확히 일치하는 '국가명-지역명' 형태로 교정(Parsing)해주세요.\n"
        f"<보유 장소 목록>: {existing_locations}\n"
        "규칙 1: 목록에 정규화된 이름이 존재한다면, 목록의 텍스트와 100% 동일한 문자열을 반환하세요.\n"
        "규칙 2: 목록에 아예 없는 완전한 신규 국가/도시라면, '국가명-지역명' 포맷을 유지하여 새로 창조하세요.\n"
        "규칙 3: 불필요한 부연 설명이나 마크다운 없이 오직 교정된 '문자열 1줄'만 반환하세요."
    )
    
    # Gemini API 초기화 (환경변수나 키 필요 시 세팅됨. 시스템에 이미 GEMINI_API_KEY 존재)
    model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
    response = model.generate_content(prompt)
    
    parsed_loc = response.text.strip().replace("\n", "").replace("\"", "")
    return parsed_loc

parsed_location = simulate_gemini_parsing(user_input)
print(f"[*] Step A (main.py -> Gemini): '{user_input}' -> '{parsed_location}' 로 변환 완료!")

# --- Step B: feedback_processor_v2.py EXIF (Geolocator -> ExifTool 덮어쓰기) 시뮬레이션 ---
print("\n[*] Step B (Geocoding & ExifTool): EXIF 메타데이터 주입 개시...")
geolocator = Nominatim(user_agent="guma_photo_organizer")
# 지역에서 "-" 제거하여 오픈스트리트맵이 알아먹기 쉬운 포맷으로 변경
search_addr = parsed_location.replace("-", " ") 
try:
    location_data = geolocator.geocode(search_addr, language='ko', timeout=10)
    if location_data:
        lat = location_data.latitude
        lon = location_data.longitude
        print(f"   [+] Geocoding 성공: '{search_addr}' -> 위도 {lat}, 경도 {lon}")
        
        # 방향 판별 (N/S, E/W) - ExifTool이 +,-도 처리 능력이 있지만 표준 텍스트 방식을 명시하는게 깔끔함
        lat_ref = 'N' if lat >= 0 else 'S'
        lon_ref = 'E' if lon >= 0 else 'W'
        
        for fpath in TARGET_FILES:
            # ExifTool 서브프로세스 호출
            # exiftool -GPSLatitude=숫자 -GPSLatitudeRef=문자 -GPSLongitude=숫자 -GPSLongitudeRef=문자 -overwrite_original "파일경로"
            cmd = [
                "exiftool",
                f"-GPSLatitude={abs(lat)}",
                f"-GPSLatitudeRef={lat_ref}",
                f"-GPSLongitude={abs(lon)}",
                f"-GPSLongitudeRef={lon_ref}",
                "-overwrite_original",
                fpath
            ]
            print(f"   [+] ExifTool Stamping: {os.path.basename(fpath)}")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        print(f"   [-] Geocoding 실패: '{search_addr}'의 위경도를 오픈스트리트맵에서 찾을 수 없습니다.")
except Exception as e:
    print(f"   [-] Geocoding/ExifTool 에러: {e}")

print("\n[*] 모든 시뮬레이션이 종료되었습니다. Result 폴더를 확인해 EXIF를 검증하십시오.")
