import subprocess
import os
from geopy.geocoders import Nominatim

class MetadataEditor:
    @staticmethod
    def stamp_metadata(filepath_list, target_date=None, target_location=None):
        """
        파일의 EXIF(사진 속성) 데이터를 강제로 주입/수정하는 독립형 모듈
        """
        print(f"  [MetadataEditor] {len(filepath_list)}개의 파일에 대하여 메타데이터 수정 작업 착수...")
        
        # 1. 위치 정보가 넘어왔다면 위도/경도로 변환 준비
        lat, lon = None, None
        if target_location and "Unknown" not in target_location:
            import re
            match = re.search(r'^\[([-\d\.]+),\s*([-\d\.]+)\]\s*(.*)$', target_location)
            if match:
                lat = float(match.group(1))
                lon = float(match.group(2))
                target_location = str(match.group(3)).strip()
                print(f"    [+] 수동 타겟 GPS 좌표 파싱 성공: 위도 {lat}, 경도 {lon}, 명칭: {target_location}")
            else:
                geolocator = Nominatim(user_agent="guma_photo_metadata_editor")
                parts = target_location.split("-", 1)
                query = {"country": parts[0].strip(), "city": parts[1].strip()} if len(parts) == 2 else {"q": target_location.replace("-", " ")}
                    
                try:
                    loc_data = geolocator.geocode(query, language='ko', timeout=10)
                    if not loc_data and len(parts) == 2:
                        loc_data = geolocator.geocode({"q": target_location.replace("-", " ")}, language='ko', timeout=10)
                    if loc_data:
                        lat, lon = loc_data.latitude, loc_data.longitude
                except Exception as e:
                    print(f"    [-] 지오코딩 변환(Nominatim) 중 에러 발생: {e}")

        # 2. ExifTool 일괄 묶음 처리 (Batch Processing)
        cmd = ["exiftool", "-m", "-overwrite_original"]
        has_update = False
        
        if lat is not None and lon is not None:
            lat_ref, lon_ref = ('N', 'E') if lat >= 0 and lon >= 0 else ('S', 'W')
            if lat < 0 and lon >= 0: lat_ref, lon_ref = 'S', 'E'
            if lat >= 0 and lon < 0: lat_ref, lon_ref = 'N', 'W'
            if lat < 0 and lon < 0: lat_ref, lon_ref = 'S', 'W'
            
            cmd.extend([
                f"-GPSLatitude={abs(lat)}", f"-GPSLatitudeRef={lat_ref}", 
                f"-GPSLongitude={abs(lon)}", f"-GPSLongitudeRef={lon_ref}"
            ])
            has_update = True
            
        if target_date and "Unknown" not in target_date:
            parts = target_date.split("-")
            yyyy = parts[0]
            mm = parts[1] if len(parts) > 1 else "01"
            dd = parts[2] if len(parts) > 2 else "15"
            exif_time = f"{yyyy}:{mm}:{dd} 12:00:00"
            # -DateTimeOriginal과 -CreateDate 동시 타겟팅
            cmd.extend([f"-DateTimeOriginal={exif_time}", f"-CreateDate={exif_time}"])
            has_update = True
        
        modified_count = 0
        if has_update and filepath_list:
            # 존재하고 유효한 파일들만 추출
            valid_files = [f for f in filepath_list if os.path.exists(f)]
            if valid_files:
                # 윈도우 커맨드 길이 제한 방지를 위해 100개씩 청크(Batch) 단위로 쪼개서 실행
                batch_size = 100
                for i in range(0, len(valid_files), batch_size):
                    batch = valid_files[i:i+batch_size]
                    batch_cmd = list(cmd) + batch
                    try:
                        subprocess.run(batch_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        modified_count += len(batch)
                    except Exception as e:
                        print(f"    [-] ExifTool Batch 실행 중 에러 발생: {e}")
                        
        print(f"    [+] 총 {modified_count}개의 파일 EXIF 강제 주입 성공")
        return modified_count
