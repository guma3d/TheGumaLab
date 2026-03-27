from fastapi import APIRouter
import multiprocessing
import os
import time
import shutil
import hashlib
import cv2
import numpy as np
import imagehash
from PIL import Image
from datetime import datetime
import exifread
import re
from typing import Any
from geopy.geocoders import Nominatim

# AI Models
from insightface.app import FaceAnalysis
import torch
from hsemotion.facial_emotions import HSEmotionRecognizer

# SQLAlchemy ORM (DEPRECATED & REMOVED)
# from core.database import SessionLocal
# from core.models import Photo

router = APIRouter()

# 설정
SOURCE_DIR = "/app/data/uploads_raw"     
TARGET_DIR = "/app/data/organized"       
JUNK_DIR = "/app/data/junk_screenshots"  
SIMILAR_DIR = "/app/data/b_cuts"         

class OrganizerPipeline:
    def __init__(self):
        print("[*] 파이프라인(ORM 기반)을 초기화합니다...")
        self.face_app: Any = None
        self.geolocator: Any = None
        self.geocode_cache = {}
        self.ensure_dirs()

    def ensure_dirs(self):
        for d in [SOURCE_DIR, TARGET_DIR, JUNK_DIR, SIMILAR_DIR]:
            os.makedirs(d, exist_ok=True)

    def load_ai_models(self):
        if self.face_app is None:
            print("[*] 🤖 AI 스캐너 (InsightFace & HSEmotion) 가동 중...")
            self.face_app = FaceAnalysis(name='buffalo_l', root='/root/.insightface')
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))
            
            _original_load = torch.load
            torch.load = lambda *a, **k: _original_load(*a, weights_only=False, **{key:val for key,val in k.items() if key != 'weights_only'})
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.emotion_recognizer = HSEmotionRecognizer(model_name='enet_b0_8_best_vgaf', device=device)
            torch.load = _original_load

    def get_file_hash(self, filepath):
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def is_junk_or_duplicate(self, filepath):
        if "_fbpass_" in os.path.basename(filepath):
            return False, self.get_file_hash(filepath)
            
        file_hash = self.get_file_hash(filepath)
        
        # [신규 아키텍처] Qdrant Payload Hash 중복 체크 (SQLite 완전 소각)
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            q_url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
            client = QdrantClient(url=q_url, timeout=3)
            res, _ = client.scroll(
                collection_name="gumaphoto_hybrid_kr", 
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="hash", match=models.MatchValue(value=file_hash))]
                ), 
                limit=1,
                with_payload=False, 
                with_vectors=False
            )
            if len(res) > 0:
                print(f"  [-] Qdrant 중복 해시 탐지: {file_hash}")
                return True, "DUPLICATE"
        except Exception as e:
            # Qdrant 연결 오류 시 패스
            pass
            
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.mkv']:
            if 'screenrecording' in os.path.basename(filepath).lower():
                return True, "SCREENRECORDING_VIDEO"
            return False, file_hash

        try:
            img = Image.open(filepath)
            width, height = img.size
            process_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
            if process_ratio > 3.0: 
                return True, "SCREENSHOT"
        except:
            pass
            
        cv_img = cv2.imread(filepath)
        if cv_img is not None:
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score < 15.0: 
                return True, f"EXTREME_BLUR_SCORE_{blur_score:.1f}"
            
        return False, file_hash

    def extract_datetime_and_location(self, filepath):
        import subprocess
        import json
        
        dt_str = "Unknown-Year"
        loc_str = "Unknown-Location"
        lat, lon = None, None

        try:
            cmd = ["exiftool", "-j", "-c", "%+.6f", "-DateTimeOriginal", "-CreateDate", "-GPSLatitude", "-GPSLongitude", "-Location", filepath]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)[0]
                
                date_val = data.get('DateTimeOriginal') or data.get('CreateDate')
                if date_val:
                    raw_dt = str(date_val).split(' ')[0]
                    parts = raw_dt.split(':')
                    if len(parts) >= 2:
                        dt_str = f"{parts[0]}-{parts[1]}"
                    else:
                        dt_str = raw_dt.replace(':', '-')
                        
                valid_loc_key = 'Location' if 'Location' in data else 'XMP:Location' if 'XMP:Location' in data else None
                if valid_loc_key:
                    loc_str = str(data[valid_loc_key]).strip()
                    if loc_str:
                        lat = None  
                        lon = None
                        
                lat_key = 'GPSLatitude' if 'GPSLatitude' in data else 'EXIF:GPSLatitude' if 'EXIF:GPSLatitude' in data else 'Composite:GPSLatitude' if 'Composite:GPSLatitude' in data else None
                lon_key = 'GPSLongitude' if 'GPSLongitude' in data else 'EXIF:GPSLongitude' if 'EXIF:GPSLongitude' in data else 'Composite:GPSLongitude' if 'Composite:GPSLongitude' in data else None
                
                # Location 텍스트가 명시적으로 없는 경우에만 GPS 좌푯값 파싱 (lat=None 일 때만)
                if lat_key and lon_key and (not loc_str or loc_str == "Unknown-Location"):
                    lat_str = str(data[lat_key]).replace('+', '')
                    lon_str = str(data[lon_key]).replace('+', '')
                    lat = float(lat_str)
                    lon = float(lon_str)
        except Exception as e:
            pass

        if dt_str == "Unknown-Year":
            parent_dir = os.path.basename(os.path.dirname(filepath))
            grandparent_dir = os.path.basename(os.path.dirname(os.path.dirname(filepath)))
            match = re.search(r'(19|20)\d{2}[-._]?\d{0,2}', parent_dir + grandparent_dir)
            if match:
                dt_str = match.group().replace('_', '-').replace('.', '-').rstrip('-')
                
        if lat is not None and lon is not None:
            if lat != 999.0:
                try:
                    loc_str = self.get_location_name(lat, lon)
                except Exception:
                    pass
        
        loc_str = re.sub(r'[\\/:*?"<>|]+', '-', loc_str)
        return dt_str, loc_str

    def get_location_name(self, lat, lon):
        cache_key = f"{round(lat, 3)},{round(lon, 3)}"
        if cache_key in self.geocode_cache:
            return self.geocode_cache[cache_key]

        if self.geolocator is None:
            self.geolocator = Nominatim(user_agent="guma_photo_organizer")
            
        try:
            time.sleep(1.1)
            location = self.geolocator.reverse((lat, lon), language='ko', timeout=10)
            if not location:
                return "Unknown-Location"
                
            addr = location.raw.get('address', {})
            city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county')
            state = addr.get('state') or addr.get('country')
            
            if city and state:
                raw_loc = f"{state}-{city}"
            elif state:
                raw_loc = state
            elif city:
                raw_loc = city
            else:
                raw_loc = "Unknown-Location"
                
            formatted_name = raw_loc.replace(' ', '-')
            self.geocode_cache[cache_key] = formatted_name
            return formatted_name
        except Exception:
            return "Unknown-Location"

    def generate_clean_filename(self, dt_str, sequence_idx, original_ext):
        return f"{dt_str}_{sequence_idx:02d}{original_ext}"

    def process_file_metadata(self, filepath):
        is_junk, junk_reason = self.is_junk_or_duplicate(filepath)
        if is_junk:
            return {"status": "JUNK", "reason": junk_reason}

        dt_str, loc_str = self.extract_datetime_and_location(filepath)
        original_context = os.path.basename(os.path.dirname(filepath))
        
        return {
            "status": "VALID",
            "dt_str": dt_str,
            "loc_str": loc_str,
            "hash": junk_reason, 
            "original_context": original_context
        }

    def run(self, batch_size=200):
        print("🚀 [GumaPhoto Pipeline] 데이터 정리를 시작합니다...")
        
        # db = SessionLocal() # Removed ORM
        total_processed_in_this_run = 0
        try:
            while True:
                all_files = []
                for root, _, files in os.walk(SOURCE_DIR):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.heic', '.mp4', '.mov', '.avi', '.mkv']:
                            all_files.append(os.path.join(root, file))
                
                if not all_files:
                    print("\n✅ 모든 파일 물리적 하드디스크 이동 완료! 대기열이 텅 비었습니다.")
                    # 🔗 이벤트 퍼블리시 (Event-Driven Architecture)
                    # 이 다음 타자인 VectorIndexer를 직접 부르지 않고, 허공에 "FileOrganized" 방송을 쏩니다!
                    if total_processed_in_this_run > 0:
                        from core.events import publish_event
                        publish_event("FileOrganized", {"total_items_organized": total_processed_in_this_run})
                    break
                    
                batch_files = all_files[:batch_size]
                print(f"\n[*] 📦 새 배치 스캔 시작: {len(batch_files)}장 / 총 남은 파일 {len(all_files)}장")
                
                date_groups = {}
                junk_count = 0
                
                for i, filepath in enumerate(batch_files):
                    if (i+1) % 50 == 0:
                        print(f"   ⏳ 메타데이터 추출 중... ({i+1}/{len(batch_files)})")
        
                    meta = self.process_file_metadata(filepath)
                    
                    if meta["status"] == "JUNK":
                        junk_count += 1
                        try: os.remove(filepath)
                        except: pass
                        continue
                    
                    dt_key = meta["dt_str"]
                    if dt_key not in date_groups:
                        date_groups[dt_key] = []
                        
                    date_groups[dt_key].append({
                        "filepath": filepath,
                        "loc_str": meta["loc_str"],
                        "hash": meta["hash"],
                        "original_context": meta["original_context"]
                    })
                    
                print(f"[*] 스캔 완료. 찌꺼기 {junk_count}개 삭제됨. 이제 하드디스크 이동을 시작합니다.")
                
                for date, items in date_groups.items():
                    for index, item in enumerate(items):
                        ext = os.path.splitext(item["filepath"])[1].lower()
                        
                        date_str = str(date)
                        if re.match(r'^(19|20)\d{2}', date_str):
                            year_folder = date_str.split('-')[0].split('_')[0]
                        else:
                            year_folder = 'Unknown-Year'
                        
                        target_folder_path = os.path.join(TARGET_DIR, year_folder, f"{date}_{item['loc_str']}")
                        os.makedirs(target_folder_path, exist_ok=True)
        
                        sequence = 1
                        while True:
                            new_filename = self.generate_clean_filename(date, sequence, ext)
                            base_filename = os.path.splitext(new_filename)[0]
                            
                            import glob
                            matching_files = glob.glob(os.path.join(target_folder_path, f"{base_filename}.*"))
                            if len(matching_files) == 0:
                                final_move_path = os.path.join(target_folder_path, new_filename)
                                break
                            sequence += 1
                        
                        try:
                            shutil.move(item['filepath'], final_move_path)
                            
                            width, height, file_size_bytes = 0, 0, 0
                            file_size_bytes = os.path.getsize(final_move_path)
                            
                            # 썸네일 즉시 굽기 및 해상도 추출
                            try:
                                from PIL import Image
                                from pillow_heif import register_heif_opener
                                register_heif_opener()
                                
                                orig_ext = ext.replace('.', '').lower()
                                thumb_path = os.path.splitext(final_move_path)[0] + f"_{orig_ext}.webp"
                                
                                with Image.open(final_move_path) as img:
                                    from PIL import ImageOps
                                    img = ImageOps.exif_transpose(img)
                                    width, height = img.size
                                    
                                    if not os.path.exists(thumb_path):
                                        img.thumbnail((300, 300))
                                        if img.mode in ("RGBA", "P"):
                                            img = img.convert("RGB")
                                        img.save(thumb_path, "WEBP", quality=75)
                            except Exception as thumb_e:
                                print(f"   ⚠️ 썸네일 파싱 실패 (동영상이거나 손상): {thumb_e}")
                                
                            # [신규 아키텍처] SQLite 통폐합으로 인해 기록 과정 폭파. 
                            # 단순히 폴더 이동만 완료하면, 나중에 vector_indexer 가 Qdrant 존재여부를 스캔하여 알아서 인제스트합니다.
                            total_processed_in_this_run += 1
                            file_hash_val = item.get('hash', 'UNKNOWN_HASH')
                                
                        except Exception as e:
                            print(f"   ⚠️ 폴더 반영 실패: {os.path.basename(item['filepath'])} -> {e}")
                            
                print(f"[*] ✅ 배치 이동 완료! (배치 끝)")
                
        finally:
            pass # db.close() Removed ORM

@router.post("/api/system/organizer/run")
async def trigger_run_organizer_task():
    from api.tasks import run_organizer_job
    run_organizer_job.delay()
    return {"message": "✅ Organizer background job queued successfully via Celery."}

def run_organizer_task():
    pipeline = OrganizerPipeline()
    pipeline.run()
    
    # [백엔드 자동 청소 로직] 이삿짐 이동이 모두 끝난 후 생긴 '빈 깡통 폴더들'을 OS 단에서 파쇄
    cleanup_dirs = ["/app/data/uploads_raw", "/app/data/organized"]
    for cln_dir in cleanup_dirs:
        if not os.path.exists(cln_dir): continue
        for dirpath, dirnames, filenames in os.walk(cln_dir, topdown=False):
            # 루트 폴더 자체는 지워지지 않도록 완벽한 절대경로 보호막(Shield) 구축
            if os.path.abspath(cln_dir) == os.path.abspath(dirpath): continue 
            
            # [도커 볼륨 구조 치명타 방어] organized 내부를 뒤지다가 발견된 uploads_raw도 삭제 금지!
            if os.path.basename(dirpath) == "uploads_raw": continue
            
            if not os.listdir(dirpath):
                try:
                    os.rmdir(dirpath)
                    print(f"🧹 [청소 완료] 텅 빈 깡통 폴더 영구 파쇄: {os.path.basename(dirpath)}")
                except: pass
