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
                
                parent_dir = os.path.basename(os.path.dirname(filepath))
                location_str = "Unknown Location"
                date_str = "Unknown Date"
                if "_" in parent_dir:
                    parts = parent_dir.split("_", 1)
                    if re.match(r'^(19|20)\d{2}', parts[0]): date_str = parts[0]
                    if len(parts) > 1 and parts[1] != "Unknown-Location" and parts[1] != "Unknown-Year":
                        location_str = parts[1]
                        
                sort_date = 0
                if date_str != "Unknown Date":
                    match_sd = re.search(r'(19|20)\d{2}(-\d{2})?(-\d{2})?', date_str)
                    if match_sd:
                        sd_full = match_sd.group(0)
                        sd_parts = sd_full.split('-')
                        sd_yr, sd_mo, sd_dy = int(sd_parts[0]), int(sd_parts[1]) if len(sd_parts) > 1 else 1, int(sd_parts[2]) if len(sd_parts) > 2 else 1
                        sort_date = sd_yr * 10000 + sd_mo * 100 + sd_dy
                if sort_date == 0:
                    try:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                        sort_date = dt.year * 10000 + dt.month * 100 + dt.day
                    except Exception: sort_date = 0

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
                    "caption": scene_caption
                }
                payload.update(best_face_payload)
                
                successful_payloads.append((filepath, payload, face_count))
                points_to_upsert.append(PointStruct(id=point_id, vector=vectors, payload=payload))
                
            except Exception as e:
                print(f"      ⚠️ 개별 항목 payload 병합 오류 (Skip): {e}")
                self.tracker.mark_error(filepath)
                
        # 3. Qdrant & DB Updates
        if points_to_upsert:
            try:
                self.qdrant.upsert_batch(points_to_upsert)
                
                db_records = []
                for filepath, payload, face_count in successful_payloads:
                    try:
                        generate_xmp_sidecar(filepath, payload)
                        
                        orig_ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ""
                        base_name = os.path.splitext(filepath)[0]
                        thumb_path = f"{base_name}_{orig_ext}.webp"
                        if not os.path.exists(thumb_path):
                            with Image.open(filepath) as t_img:
                                t_img = ImageOps.exif_transpose(t_img)
                                t_img.thumbnail((300, 300))
                                if t_img.mode in ("RGBA", "P"): t_img = t_img.convert("RGB")
                                t_img.save(thumb_path, "WEBP", quality=75)
                                
                        db_records.append((filepath, 'DONE', face_count))
                    except Exception as xmp_e:
                        print(f"      ⚠️ XMP/WEBP 발생오류: {xmp_e}")
                        db_records.append((filepath, 'ERROR', face_count))
                        
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
                            self.tracker.mark_done(filepath)
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
                            self.tracker.mark_error(filepath)
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
        for y in os.listdir(TARGET_DIR):
            yp = os.path.join(TARGET_DIR, y)
            if os.path.isdir(yp):
                for d in os.listdir(yp):
                    if '_' in d: locs.add(d.split('_', 1)[1])
        try:
            with open("/app/data/available_tags.json", "w", encoding="utf-8") as f:
                json.dump({"locations": list(locs)}, f, ensure_ascii=False)
            print(f"  [+] 총 {len(locs)}개의 로케이션 태그가 생성되었습니다.")
        except Exception: pass
            
        print("\n✅ 모든 벡터 데이터베이스 컴파일 완료!")

def run_indexing_pipeline():
    orchestrator = VectorIndexerOrchestrator()
    orchestrator.run()
