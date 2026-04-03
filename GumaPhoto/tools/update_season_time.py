import os
import sys
import subprocess
import json
from qdrant_client import QdrantClient
from qdrant_client.http.models import UpdateStatus
import re

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")  # For local testing if needed
COLLECTION_NAME = "gumaphoto_hybrid_kr"

def extract_time_and_season(filepath, date_val=None):
    season = "Unknown"
    time_of_day = "Unknown"
    
    if date_val:
        try:
            parts = str(date_val).split(' ')
            if len(parts) >= 2:
                date_part, time_part = parts[0], parts[1]
                hour = int(time_part.split(':')[0])
                if 0 <= hour < 6: time_of_day = "새벽"
                elif 6 <= hour < 12: time_of_day = "아침"
                elif 12 <= hour < 18: time_of_day = "낮"
                else: time_of_day = "밤/저녁"
                
                month_str = date_part.split(':')[1] if ':' in date_part else date_part.split('-')[1]
                month = int(month_str)
                if month in [3, 4, 5]: season = "봄"
                elif month in [6, 7, 8]: season = "여름"
                elif month in [9, 10, 11]: season = "가을"
                elif month in [12, 1, 2]: season = "겨울"
        except Exception:
            pass

    if season == "Unknown":
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
        
    if season == "Unknown":
        match = re.search(r'(19|20)\d{2}-(\d{2})', filepath)
        if match:
            month = int(match.group(2))
            if month in [3, 4, 5]: season = "봄"
            elif month in [6, 7, 8]: season = "여름"
            elif month in [9, 10, 11]: season = "가을"
            elif month in [12, 1, 2]: season = "겨울"
            
    return time_of_day, season

def update_season_and_time():
    print("🚀 [시작] DB 전체 '계절' 및 '시간대' 안전 업데이트 작업을 시작합니다.")
    qc = QdrantClient(url=QDRANT_URL, timeout=30)
    
    # 1. 모든 Qdrant DB 포인트 추출
    points = []
    offset = None
    print("   [*] DB에서 전체 데이터를 스크롤 중...")
    while True:
        res, offset = qc.scroll(
            collection_name=COLLECTION_NAME,
            limit=500,
            with_payload=True,
            with_vectors=False,
            offset=offset
        )
        points.extend(res)
        if offset is None:
            break
            
    print(f"   [*] 총 {len(points)} 개의 사진 데이터를 발견했습니다.")
    print("   [*] ExifTool 기반 배치 처리를 시작합니다...")
    
    BATCH_SIZE = 100
    updated_count = 0
    
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i:i+BATCH_SIZE]
        id_map = {}
        batch_filepaths = []
        
        for pt in batch:
            fp = pt.payload.get("filepath")
            if fp and os.path.exists(fp):
                batch_filepaths.append(fp)
                id_map[fp] = pt.id
                
        if not batch_filepaths:
            continue
            
        sys.stdout.write(f"\r   ⏳ 진행 중: {i+len(batch)} / {len(points)}")
        sys.stdout.flush()
            
        # ExifTool 호출
        try:
            cmd = ["exiftool", "-j", "-DateTimeOriginal", "-CreateDate"] + batch_filepaths
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if res.returncode == 0 and res.stdout.strip():
                parsed_list = json.loads(res.stdout)
                
                for f_data in parsed_list:
                    fpath = f_data.get("SourceFile", "")
                    if fpath not in id_map:
                        fpath = os.path.abspath(fpath) # Try fallback
                    
                    point_id = id_map.get(fpath)
                    if not point_id: continue
                        
                    date_val = f_data.get('DateTimeOriginal') or f_data.get('CreateDate')
                    
                    time_of_day, season = extract_time_and_season(fpath, date_val=date_val)
                    
                    if season != "Unknown" or time_of_day != "Unknown":
                        # 오직 'season'과 'time_of_day' 필드만 업데이트 (set_payload 연산은 병합을 수행하므로 타 필드 보존)
                        update_payload = {
                            "season": season,
                            "time_of_day": time_of_day
                        }
                        qc.set_payload(
                            collection_name=COLLECTION_NAME,
                            payload=update_payload,
                            points=[point_id]
                        )
                        updated_count += 1
                        
        except Exception as e:
            print(f"\n      ⚠️ 배치 추출 오류: {e}")
            
    print(f"\n✅ 완료! 총 {updated_count} 개의 사진에 대한 계절/시간대 데이터가 안전하게 주입되었습니다.")

if __name__ == "__main__":
    update_season_and_time()
