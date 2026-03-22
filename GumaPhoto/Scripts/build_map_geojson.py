import os
import json
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GeoJSON-Builder")

LIBRARY_DIR = "/app/data/organized"
GEOJSON_OUT = "/app/frontend/photos_map.geojson"

def build():
    logger.info("📡 Scanning all photos for GPS coordinates (Batch WGS84 Extractor)...")
    
    # ExifTool을 사용하여 디렉토리 내의 모든 사진에서 GPS 위경도를 고속으로 추출 (-r 재귀, -j Json 출력)
    cmd = [
        "exiftool", "-j", 
        "-c", "%+.6f", 
        "-GPSLatitude", "-GPSLongitude", 
        "-r", LIBRARY_DIR
    ]
           
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if not res.stdout.strip():
            logger.error("Exiftool returned empty output.")
            return
            
        try:
            data = json.loads(res.stdout)
        except json.JSONDecodeError:
            logger.error("Failed to parse Exiftool JSON output.")
            return
        
        features = []
        for item in data:
            lat = item.get("GPSLatitude")
            lon = item.get("GPSLongitude")
            
            if lat is None or lon is None:
                continue
                
            try:
                lat_f = float(str(lat).replace('+',''))
                lon_f = float(str(lon).replace('+',''))
                
                # 쓰레기 값 필터링
                if lat_f == 0.0 and lon_f == 0.0:
                    continue
                    
                path = item.get("SourceFile", "")
                rel_path = path.replace("/app/data/organized/", "")
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon_f, lat_f]  # GeoJSON 스펙은 [경도, 위도]
                    },
                    "properties": {
                        "path": rel_path
                    }
                })
            except Exception as e:
                logger.warning(f"Error parsing coordinates for {item.get('SourceFile')}: {e}")
                
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        with open(GEOJSON_OUT, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)
            
        logger.info(f"✅ GeoJSON 스키마 적재 완료! 총 {len(features)}개의 물리적 좌표 마커를 생성했습니다.")
        logger.info(f"   => 저장 위치: {GEOJSON_OUT}")

    except Exception as e:
        logger.error(f"Error executing extraction pipeline: {e}")

if __name__ == "__main__":
    build()
