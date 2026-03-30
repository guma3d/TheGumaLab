import os
import re
import subprocess
import shutil
import concurrent.futures
import json
import urllib.request
import urllib.parse

PROCESS_DIR = "/process"

def process_single_image(filepath, f, folder_name, date_pattern, cached_places):
    try:
        date_to_write = None
        # Date 체크
        result = subprocess.run(["exiftool", "-DateTimeOriginal", "-s3", filepath], capture_output=True, text=True, timeout=10)
        if not result.stdout.strip():
            # 누락된 경우 날짜 파싱 시도
            pure_date_string = f.split('_')[0]
            match = date_pattern.search(pure_date_string)
            if not match:
                pure_folder_date = folder_name.split('_')[0]
                match = date_pattern.search(pure_folder_date)
            
            if match:
                yyyy = match.group(1)
                mm = match.group(2) if match.group(2) else "01"
                dd = match.group(3) if match.group(3) else "01"
                date_to_write = f"{yyyy}:{mm}:{dd} 12:00:00"

        loc_to_write = None
        # Location 체크 (기존 XMP 확인 로직 제거, 순수 GPS만 확인)
        if folder_name in cached_places:
            result_loc = subprocess.run(["exiftool", "-GPSLatitude", "-s3", filepath], capture_output=True, text=True, timeout=10)
            if not result_loc.stdout.strip():
                loc_to_write = cached_places[folder_name]

        if not date_to_write and not loc_to_write:
            return "skipped", None

        # -overwrite_original 로 백업 생성을 막습니다.
        cmd = ["exiftool", "-m", "-overwrite_original"]
        if date_to_write:
            cmd.extend([f"-DateTimeOriginal={date_to_write}", f"-CreateDate={date_to_write}"])
        if loc_to_write:
            lat = float(loc_to_write["lat"])
            lon = float(loc_to_write["lon"])
            lat_ref = "N" if lat >= 0 else "S"
            lon_ref = "E" if lon >= 0 else "W"
            cmd.extend([
                f"-GPSLatitude={abs(lat)}",
                f"-GPSLatitudeRef={lat_ref}",
                f"-GPSLongitude={abs(lon)}",
                f"-GPSLongitudeRef={lon_ref}"
            ])
            
        cmd.append(filepath)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "modified", "OK"
            
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

    # 2. 대화형 장소(Location) 캐싱 (카카오 API)
    print("\n[2단계] 폴더명 기반 장소(Location) 대화형 매핑")
    cached_places = {}
    KAKAO_KEY = os.environ.get("KAKAO_REST_API_KEY", "")
    
    if not KAKAO_KEY:
        print("⚠️ KAKAO_REST_API_KEY 가 .env에 등록되지 않아 장소 자동 검색을 건너뜁니다.")
    else:
        unique_folders = set()
        for root, dirs, files in os.walk(PROCESS_DIR):
            if "Unknown-Year" in dirs: dirs.remove("Unknown-Year")
            if "uploads_raw" in dirs: dirs.remove("uploads_raw")
            folder_name = os.path.basename(root)
            if folder_name not in ["process", PROCESS_DIR] and "_" in folder_name:
                unique_folders.add(folder_name)
                
        for folder_name in sorted(unique_folders):
            parts = folder_name.split("_")
            if len(parts) >= 2:
                place_query = parts[1].strip()
                if not place_query: continue
                
                print(f"\n▶ 폴더명 [{folder_name}] 에서 장소 '{place_query}' 감지됨!")
                try:
                    req_url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={urllib.parse.quote(place_query)}&size=5"
                    req = urllib.request.Request(req_url)
                    req.add_header("Authorization", f"KakaoAK {KAKAO_KEY}")
                    
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode('utf-8'))
                            docs = data.get("documents", [])
                            if docs:
                                print("   0. ⏭️ 검색 건너뛰기 (장소 주입 안함)")
                                for i, doc in enumerate(docs):
                                    addr = doc.get('road_address_name') or doc.get('address_name') or '주소없음'
                                    print(f"   {i+1}. 📍 {doc['place_name']} ({addr})")
                                
                                while True:
                                    try:
                                        sel = int(input("   => 원하는 장소 번호를 선택하세요 (0~5): "))
                                        if sel == 0:
                                            print("   -> 건너뜁니다.")
                                            break
                                        elif 1 <= sel <= len(docs):
                                            selected_doc = docs[sel-1]
                                            cached_places[folder_name] = {
                                                "name": selected_doc['place_name'],
                                                "lat": selected_doc['y'],
                                                "lon": selected_doc['x']
                                            }
                                            print(f"   -> ✅ '{selected_doc['place_name']}' 선택 완료!")
                                            break
                                        else:
                                            print("   잘못된 번호입니다. 다시 입력하세요.")
                                    except ValueError:
                                        print("   숫자로 입력해주세요.")
                            else:
                                print("   -> 카카오 검색 결과가 없습니다.")
                except Exception as e:
                    print(f"   -> 카카오 API 통신 에러: {e}")

    # 3. 파일명 및 폴더명을 읽어 누락된 데이터 EXIF 주입 (초고속 멀티스레딩 엔진)
    print("\n[3단계] EXIF 메타데이터 (날짜/장소) 지능형 주입 (24-Thread 병렬 처리)")
    modified_images = 0
    skipped_images = 0
    failed_images = 0
    
    date_pattern = re.compile(r'((?:19|20)\d{2})(?:[-.]?(0[1-9]|1[0-2]))?(?:[-.]?(0[1-9]|[12]\d|3[01]))?')
    
    futures = []
    
    # 24개의 Worker를 활성화하여 동시다발적으로 I/O를 치우는 전략
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        for root, dirs, files in os.walk(PROCESS_DIR):
            if "Unknown-Year" in dirs: dirs.remove("Unknown-Year")
            if "uploads_raw" in dirs: dirs.remove("uploads_raw")
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.heic']:
                    filepath = os.path.join(root, f)
                    folder_name = os.path.basename(root)
                    futures.append(executor.submit(process_single_image, filepath, f, folder_name, date_pattern, cached_places))
                    
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
                    print(f"  ❌ 메타데이터 주입 에러: {detail}")
                    failed_images += 1

    print(f"\n✅ [멀티스레드 주입 완료]: 총 {modified_images}장의 사진에 (누락된) 날짜/장소 이식이 완료되었습니다!")
    print(f"   [패스 완료]: 기존 메타데이터가 존재하여 건너뛴 사진: {skipped_images}장")
    print(f"   [에러/실패]: 파일명에서 조건 충족 실패 등으로 실패한 사진: {failed_images}장")
    print("\n🚀 모든 전처리 과정이 완료되었습니다. 이제 이 폴더의 내용물들을 uploads_raw 로 이동하세요.")

if __name__ == "__main__":
    run_preprocessing()
