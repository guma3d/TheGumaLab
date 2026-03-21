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
        if target_location and target_location != "Unknown":
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

        modified_count = 0

        # 2. 파일별로 ExifTool 덧씌우기 수행
        for fpath in filepath_list:
            if not os.path.exists(fpath): 
                continue
                
            cmd = ["exiftool"]
            has_update = False
            
            # (A) XMP 장소명 문자열 박기
            if target_location and target_location != "Unknown":
                cmd.extend([f"-XMP:Location={target_location}"])
                has_update = True
            
            # (B) 진짜 GPS 위도경도 박기
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
                
            # (C) 사진 촬영 일자 박기
            if target_date and target_date != "Unknown":
                parts = target_date.split("-")
                yyyy = parts[0]
                mm = parts[1] if len(parts) > 1 else "01"
                dd = parts[2] if len(parts) > 2 else "15" # 중간값 15일로 배정 (안정성)
                exif_time = f"{yyyy}:{mm}:{dd} 12:00:00"
                cmd.extend([f"-DateTimeOriginal={exif_time}", f"-CreateDate={exif_time}"])
                has_update = True
            
            if has_update:
                cmd.extend(["-m", "-overwrite_original", fpath])
                try:
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    modified_count += 1
                except Exception as e:
                    print(f"    [-] ExifTool 실행 중 파일 단위 에러 발생 ({fpath}): {e}")
                    
        return modified_count
