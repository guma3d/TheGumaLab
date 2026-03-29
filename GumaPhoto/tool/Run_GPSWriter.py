import os
import sys
import json
import urllib.request
import urllib.parse
import subprocess

try:
    import exifread
    from geopy.geocoders import Nominatim
    from google import genai
except ImportError:
    print("⏳ 필요 패키지(exifread, geopy, google-genai) 자동 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "exifread", "geopy", "google-genai"])
    import exifread
    from geopy.geocoders import Nominatim
    from google import genai

import logging
logging.getLogger("exifread").setLevel(logging.CRITICAL)

LOCAL_EXIFTOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exiftool_engine", "exiftool.exe")

# 윈도우 특유의 폴더 잠김 현상(드래그 시 CWD 종속)을 완벽 차단하기 위해 툴 내부 폴더로 프로세스 위치 강제 고정
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

def load_env_key(key_name):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(key_name) or line.startswith(f"VUE_APP_{key_name}"):
                    return line.strip().split("=", 1)[1].strip('"').strip("'")
    return ""

def search_kakao(query, kakao_key):
    try:
        req_url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={urllib.parse.quote(query)}&size=5"
        req = urllib.request.Request(req_url)
        req.add_header("Authorization", f"KakaoAK {kakao_key}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("documents", [])
    except Exception as e:
        print(f"   -> 카카오 API 통신 에러: {e}")
    return []

def search_nominatim(query):
    try:
        import time
        time.sleep(1.1)
        geolocator = Nominatim(user_agent="guma_photo_gps_writer")
        location = geolocator.geocode(query, language='ko', timeout=10)
        return location
    except Exception as e:
        print(f"   -> Nominatim 지오코딩 실패: {e}")
        return None

def resolve_with_gemini(query):
    gemini_key = load_env_key("GEMINI_API_KEY")
    if not gemini_key:
         print("   -> .env 파일에 GEMINI_API_KEY 가 없습니다. AI 교정을 건너뜁니다.")
         return None, None
         
    try:
        client = genai.Client(api_key=gemini_key)
        prompt = f"사용자가 입력한 검색어: '{query}'\n이 장소의 이름이 글로벌 위성 지도 시스템(OSM/Nominatim)에서 다이렉트로 검색되지 않았습니다. 이 장소가 구글 맵 등에서 전 세계 공통으로 인식될 수 있는 '가장 정확하고 공식적인 글로벌 영문 랜드마크 명칭(Official English Name)' 또는 '도로명 영문 주소' 딱 1개만 결과로 출력하세요. 부가설명, 줄바꿈, 특수기호 절대 금지."
        resp = client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
        )
        ai_query = resp.text.strip().replace('"', '').replace("'", "")
        print(f"   => 🤖 Gemini AI가 명칭을 글로벌 규격으로 분석/변환 완료: [{ai_query}]")
        print(f"   => 🔄 자동 변환된 이름으로 위성 검색을 즉시 재시도합니다...")
        
        loc = search_nominatim(ai_query)
        return loc, ai_query
    except Exception as e:
        print(f"   -> AI 교정/변환 실패: {e}")
        return None, None

def has_gps_metadata(filepath):
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            return True
    except:
        pass
    return False

def write_exif(filepaths, pname, lat, lon):
    print(f"\n💾 총 {len(filepaths)}장의 텅 빈 사진들에 위치 정보 [{pname}] 각인 작업을 시작합니다...")
    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"
    
    success_count = 0
    failed_count = 0
    error_logs = []
    
    if not os.path.exists(LOCAL_EXIFTOOL):
        print("❌ [치명적 오류] ExifTool 엔진 실행 파일이 설치되지 않았습니다.")
        return 0, 0, ["ExifTool Missing"]

    batch_size = 50
    for i in range(0, len(filepaths), batch_size):
        batch = filepaths[i:i+batch_size]
        
        args = [
            "-m", "-overwrite_original",
            "-charset", "FileName=utf8",
            "-charset", "utf8",
            f"-XMP:Location={pname}",
            f"-GPSLatitude={abs(lat)}",
            f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLongitude={abs(lon)}",
            f"-GPSLongitudeRef={lon_ref}"
        ]
        args.extend(batch)
        args_str = "\n".join(args)
        
        try:
            res = subprocess.run([LOCAL_EXIFTOOL, "-@", "-"], input=args_str.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            
            # JPEG/JPG
            if header.startswith(b'\xff\xd8\xff'):
                if ext not in ['.jpg', '.jpeg']:
                    new_f = os.path.splitext(f)[0] + '.jpg'
            # PNG
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                if ext != '.png':
                    new_f = os.path.splitext(f)[0] + '.png'
            # HEIC / MP4 (ISO Base Media File Format)
            elif len(header) >= 8 and header[4:8] == b'ftyp':
                if ext not in ['.heic', '.heif', '.mp4', '.mov', '.m4v']:
                    new_f = os.path.splitext(f)[0] + '.heic'
            # WebP
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
        print(f"   => 🛠️ [자기 수리] 실제 포맷과 이름이 불일치하여 에러를 내던 껍데기 파일 {re_count}개의 확장자를 올바르게 강제 교정했습니다.")
        
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
        
    # 확장자-내용 불일치(카카오톡 가짜 PNG 등) 껍데기 자동 교정 수리 
    all_files = fix_extensions_automatically(all_files)
        
    print("\n🔍 스캔 중... (경고: 기존 위치정보가 박힌 사진은 보호를 위해 자동 제외합니다)")
    filepaths_to_inject = []
    skipped_count = 0
    total_scanned_files = len(all_files)
    
    for fpath in all_files:
        if has_gps_metadata(fpath):
            skipped_count += 1
        else:
            filepaths_to_inject.append(fpath)
            
    if not filepaths_to_inject:
        print(f"\n🎉 투척하신 {total_scanned_files}장의 사진 전부에 이미 위치(GPS) 정보가 안전하게 박혀있습니다! (수정 불필요)")
        return
        
    print(f"✅ 타겟 확정 완료: 총 {total_scanned_files}장 중 GPS가 없는 텅 빈 사진만 {len(filepaths_to_inject)}장 대기 중입니다.")
    if skipped_count > 0:
        print(f"   (보존 처리됨: 사진 내부에 이미 원본 GPS가 존재하던 {skipped_count}장의 사진은 자동 제외되었습니다)")
    
    query = input("\n❓ 이 빈 사진들에 주입할 장소 이름은 무엇입니까? (예: 에버랜드, 다낭, 경복궁 / 그냥 엔터시 취소): ").strip()
    
    if not query:
        print("\n❌ 검색어가 비어있어 안전을 위해 현재 작업을 취소합니다.")
        return
        
    kakao_key = load_env_key("KAKAO_REST_API_KEY")
    pname = None
    lat = None
    lon = None
    
    docs = search_kakao(query, kakao_key) if kakao_key else []
    if docs:
        print("\n🔍 국내(카카오 API) 검색 결과를 찾았습니다:")
        for i, doc in enumerate(docs):
            addr = doc.get('road_address_name') or doc.get('address_name') or '상세 주소 없음'
            print(f"   [{i+1}] 📍 {doc['place_name']} ({addr})")
        print("   [0] ⏭️ 취소하거나 해외 엔진으로 넘어가서 다시 검색하기")
        
        while True:
            sel = input("\n원하시는 장소의 번호를 선택하세요 (0~5): ").strip()
            if sel == '0':
                break
            if sel.isdigit() and 1 <= int(sel) <= len(docs):
                selected = docs[int(sel)-1]
                pname = selected['place_name']
                lat = float(selected['y'])
                lon = float(selected['x'])
                break
            print("숫자를 똑바로 입력해주세요.")
    else:
        print("\n⚠️ 카카오 API 검색 결과가 없거나(해외 지역 등) KEY 연동이 누락되었습니다.")
        
    if not pname:
        print(f"\n🌍 대체 시스템(글로벌 Nominatim API)으로 '{query}' 위치를 전 세계 광역 검색합니다...")
        loc = search_nominatim(query)
        
        # Nominatim 실패 시 Gemini 연동 기술로 자동 변환 우회 시도
        if not loc:
            print(f"\n❌ 1차 글로벌 API 검색 실패됨. 🧠 Gemini AI 언어 신경망을 긴급 가동합니다...")
            loc, ai_query = resolve_with_gemini(query)
            if loc:
                query = ai_query  # 성공 시 쿼리를 AI가 고쳐준 이름으로 교체하여 사진에 각인되도록 함
        
        if loc:
            print(f"   => 📍 최종 위성 포착 완료: {loc.address}")
            ans = input(f"\n❓ 위 주소({loc.address}) 좌표로 원본 사진들에 덮어씌울까요? (Y/N): ").strip().upper()
            if ans in ['Y', 'YES']:
                pname = query
                lat = loc.latitude
                lon = loc.longitude
            else:
                print("\n❌ 사용자에 의해 주입이 취소되었습니다.")
                return
        else:
            print("\n❌ AI 백업 시스템으로도 검색 결과를 찾을 수 없습니다. 철자를 완전히 바꿔서 다시 시도해주세요.")
            return

    if pname and lat and lon:
        s, f, all_error_logs = write_exif(filepaths_to_inject, pname, lat, lon)
        
        print("\n" + "=" * 60)
        print("📊 [최종 위치(GPS) 작업 통계 리포트]")
        print("=" * 60)
        print(f"  ▶ 전체 스캔된 타겟 파일 수: {total_scanned_files} 장")
        print(f"  ▶ ⏭️ 기존 GPS가 보존되어 안전하게 건너뛴 사진: {skipped_count} 장")
        print(f"  ▶ ✅ 성공적으로 위치가 신규 주입된 사진: {s} 장")
        if f > 0:
            print(f"  ▶ ❌ 주입 실패(에러): {f} 장")
            if all_error_logs:
                print("     [실패 상세 사유 (수백 장일 경우 최대 5개만 로깅)]:")
                unique_errs = list(dict.fromkeys(all_error_logs))
                for err in unique_errs[:5]:
                    print(f"      └ {err}")
        print("============================================================\n")

def main():
    print("=" * 60)
    print("📍 GumaPhoto AI 융합 GPS 강제 주입기 (Continuous Injector)")
    print("=" * 60)
    
    if not os.path.exists(LOCAL_EXIFTOOL):
        print(f"❌ ExifTool 엔진({LOCAL_EXIFTOOL})이 없어서 종료합니다.")
        input("엔터를 누르면 종료됩니다...")
        return
        
    first_run = True
    while True:
        target_paths = []
        
        if first_run and len(sys.argv) > 1:
            target_paths = sys.argv[1:]
        else:
            raw_input = input("\n" + "-" * 50 + "\nGPS를 주입할 사진(여러 장) 또는 폴더를 드래그 앤 드롭 하세요.\n(종료하려면 아무것도 드래그하지 않고 그냥 '엔터키'를 치거나 'Q'를 입력하세요!)\n> ").strip()
            
            if not raw_input or raw_input.upper() in ['Q', 'QUIT', 'EXIT']:
                print("\n👋 툴을 완전하게 종료합니다. 수고하셨습니다!")
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
