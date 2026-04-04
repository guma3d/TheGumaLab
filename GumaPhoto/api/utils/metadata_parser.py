import os
import re
import json
import time

# [글로벌 캐시 경로]
OSM_CACHE_PATH = "/app/data/osm_cache.json"

class MetadataParser:
    """
    GumaPhoto 메타데이터 대통합 처리 엔진 (Single Point of Truth)
    모든 장소(Geo), 시간/계절(Time), 식별(Face) 파싱 규칙을 이곳 한 곳에서 독점 관리합니다.
    """

    _location_cache = None
    _osm_banned = False

    @classmethod
    def _load_osm_cache(cls):
        if cls._location_cache is None:
            cls._location_cache = {}
            if os.path.exists(OSM_CACHE_PATH):
                try:
                    with open(OSM_CACHE_PATH, "r", encoding="utf-8") as fm:
                        cls._location_cache = json.load(fm)
                except Exception:
                    pass

    @classmethod
    def _save_osm_cache(cls):
        if cls._location_cache is not None:
            try:
                # 볼륨 마운트 에러 방지를 위해 디렉토리 존재 확인
                os.makedirs(os.path.dirname(OSM_CACHE_PATH), exist_ok=True)
                with open(OSM_CACHE_PATH, "w", encoding="utf-8") as fm:
                    json.dump(cls._location_cache, fm, ensure_ascii=False)
            except Exception as e:
                print(f"[-] 메타데이터 파서 OSM 캐시 저장 오류: {e}")

    @classmethod
    def parse_location(cls, lat, lon):
        """
        위/경도를 받아 전역 표준 규격(국가-광역시/도-시/군/구-읍/면/동/마을)으로 번역합니다.
        가장 세밀한 단위인 (동/마을/Borough/Suburb)까지 절대 누락하지 않고 100% 잡아냅니다.
        """
        if lat is None or lon is None or lat == 999.0 or lon == 999.0:
            return "Unknown Location"

        lat_key = round(float(lat), 3)
        lon_key = round(float(lon), 3)
        cache_key = f"{lat_key}_{lon_key}"

        cls._load_osm_cache()

        if cache_key in cls._location_cache:
            return cls._location_cache[cache_key]

        try:
            import urllib.request
            import unicodedata
            import urllib.error
            import os
            from dotenv import load_dotenv

            load_dotenv() # .env 강제 로드
            kakao_key = os.environ.get("KAKAO_REST_API_KEY", "").strip()
            
            # [Tier 1] 카카오 로컬 API 무제한 고속망 (대한민국 좌표 전용)
            if kakao_key:
                try:
                    kakao_url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json?x={lon}&y={lat}"
                    kakao_req = urllib.request.Request(kakao_url, headers={"Authorization": f"KakaoAK {kakao_key}"})
                    with urllib.request.urlopen(kakao_req, timeout=5) as resp:
                        if resp.status == 200:
                            kakao_data = json.loads(resp.read().decode('utf-8'))
                            if kakao_data.get('documents'):
                                # 한국 좌표 성공! 도로명보단 지번(법정동) 주소 우선
                                addr_info = kakao_data['documents'][0].get('address')
                                if not addr_info:
                                    addr_info = kakao_data['documents'][0].get('road_address', {})

                                region_1 = addr_info.get('region_1depth_name', '')
                                region_2 = addr_info.get('region_2depth_name', '')
                                region_3 = addr_info.get('region_3depth_name', '')
                                
                                clean_parts = ["대한민국"]
                                if region_1: clean_parts.append(region_1)
                                if region_2: clean_parts.append(region_2)
                                if region_3: clean_parts.append(region_3)
                                
                                final_location_str = " ".join(clean_parts).strip()
                                cls._location_cache[cache_key] = final_location_str
                                cls._save_osm_cache()
                                print(f"\n      [🚀 카카오 초고속망 작동] {lat_key}_{lon_key} ➡️ {final_location_str}")
                                return final_location_str
                except urllib.error.HTTPError as e:
                    pass # 카카오 에러나 권한 오류 시 조용히 넘어가기
                except Exception:
                    pass
            
            # 카카오가 결과를 못 냈거나 키가 없다면 [Tier 2] 글로벌 위성망 대기
            # 429 방어 로직 탑재 (백오프 재시도 전략)
            max_retries = 3
            backoff_time = 3.0
            geo_data = None

            if not cls._osm_banned:
                for attempt in range(max_retries):
                    try:
                        time.sleep(1.5 + (attempt * 2.0)) # 점진적 슬립 증가
                        
                        req_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=jsonv2&accept-language=ko"
                        # 운영 규칙상 더 명확한 User-Agent 권장
                        req = urllib.request.Request(req_url, headers={'User-Agent': 'GumaPhoto-PersonalServerBot/3.0'})
                        
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            if resp.status == 200:
                                geo_data = json.loads(resp.read().decode('utf-8'))
                                break # 성공시 루프 탈출
                    except urllib.error.HTTPError as e:
                        if e.code == 429 or e.code == 403:
                            print(f"      [⚠️ OSM 제한] {e.code} 에러. 봇이 완전 차단되었습니다. Circuit Breaker 발동!")
                            cls._osm_banned = True # 영구 우회 스위치 ON
                            break # 루프 즉시 폭파
                        else:
                            break # 서버 다운 등 다른 에러시 즉시 루프 탈출하고 대체망 발동
            
            # OSM 최종 차단 시 무료 대체 위성망(BigDataCloud) 발동
            if not geo_data:
                if cls._osm_banned:
                    print(f"\n      [🚨 궤도 변경] OSM 차단 유지됨. 위성망(BigDataCloud)으로 직행합니다...")
                
                bdc_data = None
                bdc_backoff = 2.0
                for attempt in range(3):
                    try:
                        time.sleep(1.2 + (attempt * 2.0)) # BDC 서버 차단 방지를 위한 보수적 안전 속도 (초당 1건 미만 강제)
                        bdc_url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=ko"
                        bdc_req = urllib.request.Request(bdc_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(bdc_req, timeout=10) as resp:
                            if resp.status == 200:
                                bdc_data = json.loads(resp.read().decode('utf-8'))
                                break
                    except urllib.error.HTTPError as e:
                        if e.code == 429 or e.code == 403:
                            print(f"      [⚠️ BDC 제한] {e.code} 에러. {bdc_backoff}초 대기 후 재시도... ({attempt+1}/3)")
                            time.sleep(bdc_backoff)
                            bdc_backoff *= 2
                        else:
                            break
                    except Exception:
                        break
                        
                if not bdc_data:
                    return "Unknown Location"
                    
                country = bdc_data.get('countryName', '')
                state = bdc_data.get('principalSubdivision', '')
                city = bdc_data.get('city', '')
                suburb = bdc_data.get('locality', '')
                
                clean_parts = []
                if country: clean_parts.append(country)
                if state and state != country: clean_parts.append(state)
                if city and city != state: clean_parts.append(city)
                if suburb and suburb != city and suburb != state: clean_parts.append(suburb)
                
                final_location_str = " ".join(clean_parts) if clean_parts else "Unknown Location"
                cls._location_cache[cache_key] = final_location_str
                cls._save_osm_cache()
                print(f"      [🛰️ BDC 백업망 작동] {lat_key}_{lon_key} ➡️ {final_location_str}")
                return final_location_str

            addr = geo_data.get('address', {})
                    
            # 1. 대분류 (Country, State/Province)
            country = addr.get('country', '')
            state = addr.get('state', '') or addr.get('province', '') or addr.get('region', '')
            
            # 2. 중분류 (City, County)
            city = addr.get('city', '') or addr.get('town', '') or addr.get('county', '')
            
            # 3. 소분류 (Suburb, Borough, Village, Quarter)
            suburb = addr.get('suburb', '') or addr.get('borough', '') or addr.get('village', '') or addr.get('quarter', '')

            clean_parts = []
            if country: clean_parts.append(country)
            if state and state != country: clean_parts.append(state)
            if city and city != state: clean_parts.append(city)
            if suburb and suburb != city and suburb != state: clean_parts.append(suburb)

            if clean_parts:
                # 통일된 구분자 띄어쓰기 " " 사용
                raw_result = " ".join(clean_parts)
            else:
                raw_result = geo_data.get('display_name', "Unknown Location").split(',')[0].strip()

            # 라틴 문자(발음기호) 강제 정규화 제거
            def _remove_latin(t):
                if not isinstance(t, str): return t
                res = ""
                for c in t:
                    if 'LATIN' in unicodedata.name(c, ''):
                        res += unicodedata.normalize('NFD', c).encode('ascii', 'ignore').decode('utf-8')
                    else: 
                        res += c
                return res

            final_location_str = _remove_latin(raw_result).strip()
            
            cls._location_cache[cache_key] = final_location_str
            cls._save_osm_cache()
            
            print(f"\n      [📍 OSM 글로벌 번역기] {lat_key}_{lon_key} ➡️ {final_location_str}")
            return final_location_str
                    
        except Exception as e:
            print(f"      [-] 메타데이터 파서 OSM 역 지오코딩 장애 발생: {e}")
            
        return "Unknown Location"

    @classmethod
    def parse_time_and_season(cls, date_val=None, filepath=None):
        """
        EXIF 날짜 객체 또는 파일 경로를 분석하여 시간대(Time of day)와 계절(Season)을 뱉어냅니다.
        """
        time_of_day = "Unknown"
        season = "Unknown"

        # 1. date_val 형태가 들어온 경우 (우선)
        if date_val and str(date_val) not in ["Unknown Date", "Unknown-Year"]:
            try:
                # 형태: "2023:10:15 14:30:00" 혹은 "2023-10-15 14:30:00"
                date_str = str(date_val).strip()
                parts = date_str.split(' ')
                
                if len(parts) >= 2:
                    date_part, time_part = parts[0], parts[1]
                    
                    # 시간대 구분
                    hour = int(time_part.split(':')[0])
                    if 0 <= hour < 6: time_of_day = "새벽"
                    elif 6 <= hour < 12: time_of_day = "아침"
                    elif 12 <= hour < 18: time_of_day = "낮"
                    else: time_of_day = "밤/저녁"
                    
                    # 계절 구분 (월 기반)
                    month_str = date_part.split(':')[1] if ':' in date_part else date_part.split('-')[1]
                    month = int(month_str)
                    if month in [3, 4, 5]: season = "봄"
                    elif month in [6, 7, 8]: season = "여름"
                    elif month in [9, 10, 11]: season = "가을"
                    elif month in [12, 1, 2]: season = "겨울"
                    
                return time_of_day, season
            except Exception:
                pass

        # 2. EXIF 원본 파싱 시도 (filepath 가 주어진 경우)
        if filepath and season == "Unknown":
            try:
                import exifread
                with open(filepath, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                
                if 'EXIF DateTimeOriginal' in tags:
                    dt_str = str(tags['EXIF DateTimeOriginal'])
                    parts = dt_str.split(' ')
                    if len(parts) == 2:
                        date_part, time_part = parts[0], parts[1]
                        hour = int(time_part.split(':')[0])
                        if 0 <= hour < 6: time_of_day = "새벽"
                        elif 6 <= hour < 12: time_of_day = "아침"
                        elif 12 <= hour < 18: time_of_day = "낮"
                        else: time_of_day = "밤/저녁"
                            
                        month = int(date_part.split(':')[1])
                        if month in [3, 4, 5]: season = "봄"
                        elif month in [6, 7, 8]: season = "여름"
                        elif month in [9, 10, 11]: season = "가을"
                        elif month in [12, 1, 2]: season = "겨울"
            except Exception:
                pass

        # 3. 최후의 수단: 파일 경로명에서 년-월 유추 (예: /2012-12_San-Francisco/)
        if filepath and season == "Unknown":
            match = re.search(r'(19|20)\d{2}-(\d{2})', filepath)
            if match:
                month = int(match.group(2))
                if month in [3, 4, 5]: season = "봄"
                elif month in [6, 7, 8]: season = "여름"
                elif month in [9, 10, 11]: season = "가을"
                elif month in [12, 1, 2]: season = "겨울"

        return time_of_day, season
