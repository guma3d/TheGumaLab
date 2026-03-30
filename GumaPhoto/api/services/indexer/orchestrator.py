import os
import gc
import cv2
import uuid
import re
import numpy as np
import concurrent.futures
import threading
import queue
import exifread
import json

from PIL import Image, ImageOps
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

import torch
from qdrant_client.http.models import PointStruct

from api.services.indexer.model_florence import FlorenceEngine
from api.services.indexer.model_siglip import SigLIPEngine
from api.services.indexer.model_faces import FaceEngine
from api.services.indexer.qdrant_store import QdrantStore
from api.services.indexer.progress_tracker import ProgressTracker
from api.utils.metadata import generate_xmp_sidecar

TARGET_DIR = "/app/data/organized"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
BATCH_SIZE = 10 

class VectorIndexerOrchestrator:
    def __init__(self):
        self.qdrant = QdrantStore(QDRANT_URL)
        self.tracker = ProgressTracker()
        
        self.engine_siglip = SigLIPEngine()
        self.engine_face = FaceEngine()
        self.engine_florence = FlorenceEngine()

    def extract_time_and_season(self, filepath):
        time_of_day = "Unknown"
        season = "Unknown"
        try:
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

    def process_batch(self, valid_items):
        if not valid_items: return
            
        pil_images = [item["pil_img"] for item in valid_items]
        
        # 1. AI Models Inference
        scene_embeddings = self.engine_siglip.infer_batch(pil_images)
        captions_batch, objects_batch = self.engine_florence.infer_batch(pil_images)
        
        points_to_upsert = []
        successful_payloads = []
        
        # 2. Merge Modalities
        for i, item in enumerate(valid_items):
            try:
                filepath = item["filepath"]
                cv_img = item["cv_img"]
                point_id = item["point_id"]
                
                scene_embedding = scene_embeddings[i] if scene_embeddings[i] is not None else np.zeros(768)
                scene_caption = captions_batch[i]
                found_objects = objects_batch[i]

                face_count, found_people, best_face_vector, best_face_payload, real_age = self.engine_face.analyze_face(cv_img, filepath)
                
                vectors = {"scene": scene_embedding.tolist()}
                if best_face_vector: vectors["face"] = best_face_vector
                
                age_korean_1 = f"{real_age}세"
                age_korean_2 = f"{real_age}살"
                if age_korean_1 not in found_objects: found_objects.append(age_korean_1)
                if age_korean_2 not in found_objects: found_objects.append(age_korean_2)
                
                # [아키텍처 혁신 변경] 폴더명 의존을 완전히 폐기하고 '무조건 EXIF/XMP 메타데이터'에서 Source of Truth를 가져옵니다.
                location_str = "Unknown Location"
                date_str = "Unknown Date"
                lat_f, lon_f = None, None
                sort_date = 0
                
                try:
                    import subprocess, json
                    r = subprocess.run(["exiftool", "-j", "-c", "%+.6f", "-DateTimeOriginal", "-CreateDate", "-Location", "-XMP:Location", "-GPSLatitude", "-GPSLongitude", filepath], capture_output=True, text=True, timeout=5)
                    if r.returncode == 0 and r.stdout.strip():
                        d = json.loads(r.stdout)[0]
                        
                        # 시간/날짜 (Date) 추출
                        d_val = d.get('DateTimeOriginal') or d.get('CreateDate')
                        if d_val:
                            raw_dt = str(d_val).split(' ')[0].replace(':', '-')
                            date_str = raw_dt
                            import re
                            if re.match(r'^(19|20)\d{2}-\d{2}-\d{2}$', date_str):
                                sp = date_str.split('-')
                                sort_date = int(sp[0])*10000 + int(sp[1])*100 + int(sp[2])
                        
                        # 장소(Location) XMP 텍스트 기반 네임 파싱 완전히 폐지 (사용자 규칙: 오직 숫자 GPS 역추적만 사용)
                        location_str = "Unknown Location"
                        
                        # GPS 마커 파싱
                        lat_raw = d.get('GPSLatitude') or d.get('EXIF:GPSLatitude')
                        lon_raw = d.get('GPSLongitude') or d.get('EXIF:GPSLongitude')
                        if lat_raw and lon_raw:
                            try:
                                lat_f = float(str(lat_raw).replace('+', ''))
                                lon_f = float(str(lon_raw).replace('+', ''))
                            except ValueError: pass
                            
                        # --------------------------------------------------------------------------
                        # [ OSM 글로벌 지능형 위치 번역 캐시 시스템 (Reverse Geocoding) ]
                        # --------------------------------------------------------------------------
                        if lat_f is not None and lon_f is not None and location_str == "Unknown Location":
                            # 오차 반경 약 110m 묶음 (속도 극대화 & 차단 방지)
                            lat_key = round(lat_f, 3)
                            lon_key = round(lon_f, 3)
                            cache_key = f"{lat_key}_{lon_key}"
                            
                            if not hasattr(self, 'location_cache'):
                                self.location_cache = {}
                                
                            if cache_key in self.location_cache:
                                location_str = self.location_cache[cache_key]
                            else:
                                try:
                                    import urllib.request, time
                                    time.sleep(1.1)
                                    req_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat_f}&lon={lon_f}&format=jsonv2&accept-language=ko"
                                    req = urllib.request.Request(req_url, headers={'User-Agent': 'GumaPhotoIndexer/CacheNode'})
                                    with urllib.request.urlopen(req, timeout=5) as resp:
                                        if resp.status == 200:
                                            geo_data = json.loads(resp.read().decode('utf-8'))
                                            addr = geo_data.get('address', {})
                                            country = addr.get('country', '')
                                            city = addr.get('city', '') or addr.get('town', '') or addr.get('county', '')
                                            suburb = addr.get('suburb', '') or addr.get('borough', '') or addr.get('village', '')
                                            
                                            clean_parts = []
                                            if country: clean_parts.append(country)
                                            if city: clean_parts.append(city)
                                            if suburb: clean_parts.append(suburb)
                                            
                                            if clean_parts:
                                                self.location_cache[cache_key] = " ".join(clean_parts)
                                            else:
                                                self.location_cache[cache_key] = geo_data.get('display_name', "Unknown Location").split(',')[0].strip()
                                                
                                            location_str = self.location_cache[cache_key]
                                            print(f"      [📍 OSM 스마트 번역 성공] {lat_key}_{lon_key} ➡️ {location_str}")
                                except Exception as gc_e:
                                    print(f"      [-] OSM 역 지오코딩 1일 한도 API 에러(또는 차단): {gc_e}")
                                    self.location_cache[cache_key] = "Unknown Location"
                        # --------------------------------------------------------------------------
                                    
                except Exception as ex_e:
                    print(f"      [-] Exif parsing err (DB Sync): {ex_e}")

                if sort_date == 0:
                    try:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                        sort_date = dt.year * 10000 + dt.month * 100 + dt.day
                        if date_str == "Unknown Date":
                            date_str = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
                    except Exception: 
                        sort_date = 0

                payload = {
                    "filepath": filepath,
                    "filename": item["filename"],
                    "original_context": item["context_str"],
                    "face_count": face_count,
                    "people": found_people,
                    "date": date_str,
                    "sort_date": sort_date,
                    "location": location_str,
                    "time_of_day": item["time_of_day"],
                    "season": item["season"],
                    "objects": found_objects,
                    "caption": scene_caption,
                    "lat": lat_f,
                    "lon": lon_f
                }
                payload.update(best_face_payload)
                
                successful_payloads.append((filepath, payload, point_id))
                points_to_upsert.append(PointStruct(id=point_id, vector=vectors, payload=payload))
                
            except Exception as e:
                print(f"      ⚠️ 개별 항목 payload 병합 오류 (Skip): {e}")
                self.tracker.mark_error(filepath, str(e))
                
        # 3. Qdrant & DB Updates
        if points_to_upsert:
            try:
                self.qdrant.upsert_batch(points_to_upsert)
                
                db_records = []
                for filepath, payload, point_id in successful_payloads:
                    try:
                        print(f"  [🕵️‍♂️ AUDIT-AFTER] File: {filepath} | Loc: {payload.get('location')} | Date: {payload.get('date')} | People: {payload.get('people')}")
                        
                        try:
                            import subprocess
                            
                            def get_exif_str(f_path):
                                try:
                                    if not os.path.exists(f_path): return "File Not Found"
                                    r = subprocess.run(["exiftool", "-j", "-c", "%+.6f", "-DateTimeOriginal", "-Location", "-GPSLatitude", "-GPSLongitude", f_path], capture_output=True, text=True, timeout=5)
                                    if r.returncode == 0 and r.stdout.strip():
                                        d = json.loads(r.stdout)[0]
                                        lat = d.get("GPSLatitude", "None")
                                        lon = d.get("GPSLongitude", "None")
                                        gps = f"({lat}, {lon})" if lat != "None" else "No GPS"
                                        return f"Loc: {d.get('Location', 'None')} | GPS: {gps} | Date: {d.get('DateTimeOriginal', 'None')}"
                                except: pass
                                return "EXIF: Parse Error"

                            trace_file = "/app/data/audit_trace.json"
                            trace_id = payload.get("original_context", "")
                            if trace_id.startswith("fbtrace_") and os.path.exists(trace_file):
                                with open(trace_file, "r", encoding="utf-8") as tf:
                                    lines = tf.readlines()
                                for line in reversed(lines):
                                    data = json.loads(line)
                                    if data.get("trace_id") == trace_id:
                                        print("\n========================================================")
                                        print(f"  📊 [피드백 실시간 비교 결과 (Before vs After)]")
                                        print(f"  > 파일명: {os.path.basename(data.get('filepath'))}  ➡️  {os.path.basename(filepath)}")
                                        print(f"  > 날  짜: [{data.get('date')}]  ➡️  [{payload.get('date')}]")
                                        print(f"  > 장  소: [{data.get('location')}]  ➡️  [{payload.get('location')}]")
                                        print(f"  > 인  물: {data.get('people')}  ➡️  {payload.get('people')}")
                                        after_exif = get_exif_str(filepath)
                                        print(f"  > 물리적 메타데이터 [BEFORE]: {data.get('exif')}")
                                        print(f"  > 물리적 메타데이터  [AFTER]: {after_exif}")
                                        print("========================================================\n")
                                        try:
                                            with open(trace_file, "a", encoding="utf-8") as wf:
                                                wf.write(json.dumps({
                                                    "type": "AFTER", 
                                                    "trace_id": trace_id, 
                                                    "filepath": filepath, 
                                                    "location": payload.get('location'), 
                                                    "date": payload.get('date'), 
                                                    "people": payload.get('people'), 
                                                    "exif": after_exif
                                                }, ensure_ascii=False) + "\n")
                                        except: pass
                                        break
                        except Exception as trace_err:
                            print(f"    [-] Audit Trace Exception: {trace_err}")
                            
                        # generate_xmp_sidecar(filepath, payload) # XMP 사이드카 파일 완전 제거 정책
                        
                        orig_ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ""
                        base_name = os.path.splitext(filepath)[0]
                        thumb_path = f"{base_name}_{orig_ext}.webp"
                        if not os.path.exists(thumb_path):
                            with Image.open(filepath) as t_img:
                                t_img = ImageOps.exif_transpose(t_img)
                                t_img.thumbnail((300, 300))
                                if t_img.mode in ("RGBA", "P"): t_img = t_img.convert("RGB")
                                t_img.save(thumb_path, "WEBP", quality=75)
                                
                        db_records.append((filepath, 'DONE', point_id))
                    except Exception as xmp_e:
                        print(f"      ⚠️ XMP/WEBP 발생오류: {xmp_e}")
                        db_records.append((filepath, 'ERROR', point_id))
                        
                self.tracker.bulk_mark(db_records)
            except Exception as qdrant_err:
                print(f"    🚨 Qdrant 배치 업서트 치명적 실패: {qdrant_err}")

        # VRAM 메모리 단편화 및 좀비 텐서를 해제하여 장시간 가동 방어
        torch.cuda.empty_cache()
        gc.collect()

    def run(self):
        print("\n🚀 [3단계: 딥러닝 벡터화 파이프라인 가동]")
        all_targets = []
        for root, dirs, files in os.walk(TARGET_DIR):
            blacklist = ['OriginalSource', 'junk_screenshots', 'b_cuts', 'test_images', '.git', 'uploads_raw', 'enrolled', 'test', 'unknown']
            dirs[:] = [d for d in dirs if d not in blacklist]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.heic']:
                    all_targets.append(os.path.join(root, file))
                    
        total = len(all_targets)
        print(f"[*] 총 {total}장의 대상 사진을 발견했습니다.")
        
        batch_queue = queue.Queue(maxsize=1)

        def cpu_producer():
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                for i in range(0, total, BATCH_SIZE):
                    batch_paths = all_targets[i : i + BATCH_SIZE]
                    def prep(filepath):
                        if self.tracker.is_already_processed_db_only(filepath):
                            return None
                            
                        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
                        if self.qdrant.point_exists(point_id):
                            self.tracker.mark_done(filepath, point_id)
                            return None
                            
                        self.qdrant.delete_point(point_id)
                        self.tracker.clean_slate_for_reprocess(filepath)
                        
                        try:
                            pil_img = Image.open(filepath).convert('RGB')
                            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                            file_hash = self.tracker.get_file_hash(filepath)
                            context_str = self.tracker.get_original_context(file_hash)
                            time_of_day, season = self.extract_time_and_season(filepath)
                            
                            return {
                                "filepath": filepath, "filename": os.path.basename(filepath),
                                "pil_img": pil_img, "cv_img": cv_img,
                                "context_str": context_str, "time_of_day": time_of_day,
                                "season": season, "point_id": point_id
                            }
                        except Exception as e:
                            self.tracker.mark_error(filepath, str(e))
                            return None
                            
                    results = list(executor.map(prep, batch_paths))
                    valid_items = [r for r in results if r is not None]
                    batch_queue.put((i, valid_items))
            batch_queue.put(None)
            
        prod_thread = threading.Thread(target=cpu_producer)
        prod_thread.start()
        
        while True:
            item = batch_queue.get()
            if item is None: break
            i, valid_items = item
            if valid_items:
                print(f"\n[*] 📦 배치 진행 중: {i+1} ~ {min(i+BATCH_SIZE, total)} / {total} (실제 처리: {len(valid_items)}장)")
                self.process_batch(valid_items)
            
        prod_thread.join()
        
        locs = set()
        dates_set = set()
        print("\n[*] Qdrant 페이로드(DB)를 통한 프론트엔드 좌측 사이드바 위치 및 날짜 태그를 재구성 중입니다...")
        try:
            offset = None
            while True:
                results, offset = self.qdrant.q_client.scroll(
                    collection_name="gumaphoto_hybrid_kr",
                    scroll_filter=None,
                    limit=1000,
                    with_payload=["location", "date"],
                    with_vectors=False,
                    offset=offset
                )
                for r in results:
                    p = r.payload or {}
                    loc_val = p.get("location")
                    date_val = p.get("date")
                    
                    if loc_val and loc_val != "Unknown Location":
                        locs.add(loc_val)
                    if date_val and date_val != "Unknown Date":
                        import re
                        m = re.match(r'^(19|20)\d{2}-\d{2}', date_val)
                        if m: dates_set.add(m.group(0))
                        
                if offset is None:
                    break
                    
            with open("/app/data/available_tags.json", "w", encoding="utf-8") as f:
                json.dump({"locations": list(locs), "dates": list(dates_set)}, f, ensure_ascii=False)
            print(f"  [+] Qdrant Payload 기반 총 장소 {len(locs)}개, 날짜 {len(dates_set)}개의 태그(사이드바 뱃지)가 스크롤 생성 완료되었습니다.")
        except Exception as e:
            print(f"  [-] Qdrant 서치 및 태그 추출 실패 (태그 생성 무시됨): {e}")
            
        print("\n✅ 모든 벡터 데이터베이스 컴파일 완료!")

def run_indexing_pipeline():
    orchestrator = VectorIndexerOrchestrator()
    orchestrator.run()
