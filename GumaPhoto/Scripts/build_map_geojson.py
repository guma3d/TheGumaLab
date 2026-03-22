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
    
    cmd = [
        "exiftool", "-j", 
        "-c", "%+.6f", 
        "-GPSLatitude", "-GPSLongitude", 
        "-r", LIBRARY_DIR
    ]
           
    tmp_file = "/tmp/exif_dump.json"
    
    try:
        # Write directly to file to avoid stdout memory buffer limits
        with open(tmp_file, "w", encoding="utf-8") as out_f:
            subprocess.run(cmd, stdout=out_f, text=True)
            
        with open(tmp_file, "r", encoding="utf-8") as in_f:
            data = json.load(in_f)
            
    except Exception as e:
        logger.error(f"Failed during exiftool extraction or parsing: {e}")
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
                    "coordinates": [lon_f, lat_f]
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
    
    try:
        with open(GEOJSON_OUT, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)
            
        logger.info(f"✅ GeoJSON 스키마 적재 완료! 총 {len(features)}개의 물리적 좌표 마커를 생성했습니다.")
        logger.info(f"   => 저장 위치: {GEOJSON_OUT}")
    except Exception as e:
        logger.error(f"Failed to write output geojson: {e}")

if __name__ == "__main__":
    build()
