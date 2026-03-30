import os
import numpy as np
import cv2
import time
import hashlib
import exifread
import re
from datetime import datetime
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass
os.environ["LD_LIBRARY_PATH"] = "/usr/local/lib/python3.11/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/dist-packages/nvidia/cublas/lib:" + os.environ.get("LD_LIBRARY_PATH", "")
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from transformers import AutoProcessor, AutoModel, AutoModelForCausalLM
import transformers.dynamic_module_utils
transformers.dynamic_module_utils.check_imports = lambda x: []
from insightface.app import FaceAnalysis
import pickle
import gc
import torch
import json
import warnings

warnings.filterwarnings("ignore")

try:
    from hsemotion.facial_emotions import HSEmotionRecognizer
except ImportError:
    pass

# YOLO is removed, replaced by Florence-2-large

# ==========================================
# ⚙️ Configuration & DB Settings
# ==========================================
# 1단계 정리에서 이동/복사된 최종 폴더 (이 폴더의 사진만 스캔 대상)
TARGET_DIR = "/app/data/organized"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"
BATCH_SIZE = 15 # 한 번에 처리할 사진 수 (GPU, RAM 메모리 고려)

class VectorIndexer:
    def __init__(self, run_vision_ai=True, run_semantic_ai=True, run_facial_ai=True, run_metadata_geo=True, run_webp_thumbnail=True):
        self.run_vision_ai = run_vision_ai
        self.run_semantic_ai = run_semantic_ai
        self.skip_face = not run_facial_ai
        self.run_metadata_geo = run_metadata_geo
        self.run_webp_thumbnail = run_webp_thumbnail
        
        print(f"[*] 벡터 DB (Qdrant) 접속 초기화... ({QDRANT_URL})")
        self.q_client = QdrantClient(url=QDRANT_URL, timeout=60)
        self.init_qdrant_collection()
        
        # SQLite 대신 Qdrant 자체를 Source of Truth로 사용하여 캐싱 (초고속 O(1) 스캔)
        self.indexed_filepaths = self.load_indexed_filepaths_from_qdrant()
        self.failed_filepaths = set()
        
        if self.run_vision_ai or self.run_semantic_ai or not self.skip_face:
            self.load_ai_models()
        else:
            print("[*] 💡 시각 AI / 캡션 AI / 안면 AI 엔진이 모두 비활성화되어 모델 로드를 생략합니다. (초경량 모드)")


    def init_qdrant_collection(self):
        """다중 벡터(Multivector)를 수용할 수 있는 Qdrant 컬렉션 뼈대 생성"""
        # Qdrant v1.1.0 이상부터 Named Vectors 기능을 지원하여 한 Point 내에 여러 목적의 벡터 저장 가능
        if not self.q_client.collection_exists(collection_name=COLLECTION_NAME):
            self.q_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "scene": VectorParams(size=768, distance=Distance.COSINE),
                    "face": VectorParams(size=512, distance=Distance.COSINE)
                }
            )
            # 메타데이터 검색 속도 최적화를 위한 페이로드 인덱스 생성
            self.q_client.create_payload_index(COLLECTION_NAME, "original_context", "text")
            self.q_client.create_payload_index(COLLECTION_NAME, "filepath", "keyword")
            self.q_client.create_payload_index(COLLECTION_NAME, "people", field_schema=PayloadSchemaType.KEYWORD)
            self.q_client.create_payload_index(COLLECTION_NAME, "objects", field_schema=PayloadSchemaType.KEYWORD)
            self.q_client.create_payload_index(COLLECTION_NAME, "location", field_schema=PayloadSchemaType.TEXT)
            self.q_client.create_payload_index(COLLECTION_NAME, "caption", field_schema=PayloadSchemaType.TEXT)
            self.q_client.create_payload_index(COLLECTION_NAME, "hash", field_schema=PayloadSchemaType.KEYWORD)
            print(f"  [+] 신규 Qdrant 멀티-벡터 컬렉션 '{COLLECTION_NAME}' 생성 완료.")
        else:
            print(f"  [-] 기존 Qdrant 컬렉션 '{COLLECTION_NAME}' 을 재사용합니다.")

    def load_indexed_filepaths_from_qdrant(self):
        """시작 시 Qdrant에서 처리 완료된 파일 경로를 빨아들여 메모리에 올려둠"""
        print("[*] Qdrant에서 기존 인덱싱 된 파일 목록 캐싱 중...")
        indexed = set()
        offset = None
        while True:
            records, offset = self.q_client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                offset=offset,
                with_payload=["filepath"],
                with_vectors=False
            )
            for record in records:
                if record.payload and "filepath" in record.payload:
                    indexed.add(record.payload["filepath"])
            if offset is None:
                break
        print(f"  [+] 총 {len(indexed)}개의 기존 처리 완료 파일이 캐시되었습니다.")
        return indexed

    def load_ai_models(self):
        """🚀 SigLIP (배경/상황) & InsightFace (얼굴) & Florence-2-large 모델 VRAM 로드"""
        print("[*] 🖼️ 초정밀 SigLIP 이미지 인코더 로드 중 (google/siglip-base-patch16-224) ...")
        self.siglip_processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-224")
        self.siglip_model = AutoModel.from_pretrained("google/siglip-base-patch16-224").to('cuda' if torch.cuda.is_available() else 'cpu')
        self.siglip_model.eval()
        
        if not self.skip_face:
            try:
                from api.services.insightface_service import InsightFaceModule
                self.insightface = InsightFaceModule()
            except Exception as e:
                print(f"  [!] InsightFaceModule 로드 실패: {e}")
                self.insightface = None
        else:
            self.insightface = None
        self.family_meta = {}
        if os.path.exists("/app/data/family_meta.json"):
            with open("/app/data/family_meta.json", "r", encoding="utf-8") as f:
                self.family_meta = json.load(f)
            
        print("[*] 📝 Florence-2-base VLM 상황 묘사 AI 로드 중 ...")
        try:
            florence_model_id = "microsoft/Florence-2-base"
            self.florence_model = AutoModelForCausalLM.from_pretrained(florence_model_id, trust_remote_code=True).to("cuda" if torch.cuda.is_available() else "cpu")
            self.florence_processor = AutoProcessor.from_pretrained(florence_model_id, trust_remote_code=True)
            self.florence_model.eval()
            print("  [+] Florence-2-base 로드 완료!")
        except Exception as e:
            print(f"  [-] Florence-2-base 로딩 실패: {e}")
            self.florence_model = None
            
        print("  [+] 모든 시각 초거대 AI 모델 로딩 완료!")

    def get_original_context(self, filepath):
        """기존 SQLite 의존성을 제거하고 디렉토리명에서 문맥 추출"""
        try:
            return os.path.basename(os.path.dirname(filepath))
        except Exception:
            return "Organized_Photo"

    def get_file_hash(self, filepath):
        """파일 SHA256 해시 추출 (DB 연동 시 고유 조회용 - 1단계 Organizer와 통일)"""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as afile:
            buf = afile.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(65536)
        return hasher.hexdigest()

    def is_already_processed(self, filepath):
        """메모리에 캐싱된 Qdrant 세트를 기반으로 초고속 O(1) 중복 검사 (SQLite 종속 제거)"""
        # 만약 AI를 끈 '순수 메타데이터 업데이트 모드'라면, 기존에 처리된 파일도 일괄 강제 스캔(무조건 업데이트)합니다!
        if not (self.run_vision_ai or self.run_semantic_ai or not self.skip_face):
            return False 
            
        if filepath in self.indexed_filepaths:
            return True
        if filepath in self.failed_filepaths:
            return True
        return False


    def extract_time_and_season(self, filepath):
        """EXIF나 파일명을 기반으로 시간대(Time of Day)와 계절(Season) 추출"""
        time_of_day = "Unknown"
        season = "Unknown"
        
        # 1. EXIF에서 정확한 시간 추출 시도
        try:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            
            if 'EXIF DateTimeOriginal' in tags:
                dt_str = str(tags['EXIF DateTimeOriginal'])
                # 포맷: 2023:10:15 14:30:00
                parts = dt_str.split(' ')
                if len(parts) == 2:
                    date_part = parts[0]
                    time_part = parts[1]
                    
                    # 시간대 구분
                    hour = int(time_part.split(':')[0])
                    if 0 <= hour < 6:
                        time_of_day = "새벽"
                    elif 6 <= hour < 12:
                        time_of_day = "아침"
                    elif 12 <= hour < 18:
                        time_of_day = "낮"
                    else:
                        time_of_day = "밤/저녁"
                        
                    # 계절 구분 (월 기반)
                    month = int(date_part.split(':')[1])
                    if month in [3, 4, 5]:
                        season = "봄"
                    elif month in [6, 7, 8]:
                        season = "여름"
                    elif month in [9, 10, 11]:
                        season = "가을"
                    elif month in [12, 1, 2]:
                        season = "겨울"
        except Exception:
            pass
            
        # 2. EXIF가 날아갔다면 폴더명/파일명에서 유추 (예: /app/data/organized/2012-12_San-Francisco/2012-12_177.jpg)
        if season == "Unknown":
            import re
            match = re.search(r'(19|20)\d{2}-(\d{2})', filepath)
            if match:
                month = int(match.group(2))
                if month in [3, 4, 5]:
                    season = "봄"
                elif month in [6, 7, 8]:
                    season = "여름"
                elif month in [9, 10, 11]:
                    season = "가을"
                elif month in [12, 1, 2]:
                    season = "겨울"
                    
        return time_of_day, season

    def process_batch(self, valid_items, force_location=None, force_date=None):
        """Pre-fetched batch 단위로 메모리에 올려 병렬 연산 (CPU/GPU 동시 가동을 위함)"""
        points_to_upsert = []
        successful_payloads = []
        
        if not valid_items:
            return
            
        # print(f"   [배치 연산] 신규 스캔 묶음: {len(valid_items)}장 병렬 처리 중...")
        
        pil_images = [item["pil_img"] for item in valid_items]
        scene_embeddings = [None] * len(valid_items)
        captions_batch = [""] * len(valid_items)
        objects_batch = [[] for _ in valid_items]
        
        # --- [A] SigLIP 다중 배치 추론 ---
        if self.run_vision_ai:
            try:
                siglip_inputs = self.siglip_processor(images=pil_images, return_tensors="pt").to(self.siglip_model.device)
                with torch.no_grad():
                    out = self.siglip_model.get_image_features(**siglip_inputs)
                    emb = out / out.norm(p=2, dim=-1, keepdim=True)
                    scene_embeddings = emb.cpu().numpy()
            except Exception as e:
                print(f"      🚨 SigLIP 연산 오류: {e}")
            
        # --- [B] Florence-2 다중 배치 추론 ---
        if self.run_semantic_ai and getattr(self, "florence_model", None):
            try:
                # 캡션 다중 배치
                task_prompt_cap = "<MORE_DETAILED_CAPTION>"
                flo_inputs_cap = self.florence_processor(text=[task_prompt_cap]*len(valid_items), images=pil_images, return_tensors="pt").to(self.florence_model.device)
                with torch.no_grad():
                    generated_ids_cap = self.florence_model.generate(
                        input_ids=flo_inputs_cap["input_ids"],
                        pixel_values=flo_inputs_cap["pixel_values"],
                        max_new_tokens=512,
                        early_stopping=False,
                        do_sample=False,
                        num_beams=1,
                    )
                generated_texts_cap = self.florence_processor.batch_decode(generated_ids_cap, skip_special_tokens=False)
                for idx, text in enumerate(generated_texts_cap):
                    parsed = self.florence_processor.post_process_generation(text, task=task_prompt_cap, image_size=(pil_images[idx].width, pil_images[idx].height))
                    captions_batch[idx] = parsed.get(task_prompt_cap, "")
                    
                # 사물 태그 다중 배치
                task_prompt_od = "<OD>"
                flo_inputs_od = self.florence_processor(text=[task_prompt_od]*len(valid_items), images=pil_images, return_tensors="pt").to(self.florence_model.device)
                with torch.no_grad():
                    generated_ids_od = self.florence_model.generate(
                        input_ids=flo_inputs_od["input_ids"],
                        pixel_values=flo_inputs_od["pixel_values"],
                        max_new_tokens=1024,
                        early_stopping=False,
                        do_sample=False,
                        num_beams=1,
                    )
                generated_texts_od = self.florence_processor.batch_decode(generated_ids_od, skip_special_tokens=False)
                for idx, text in enumerate(generated_texts_od):
                    parsed = self.florence_processor.post_process_generation(text, task=task_prompt_od, image_size=(pil_images[idx].width, pil_images[idx].height))
                    od_res = parsed.get(task_prompt_od, {})
                    obj_list = []
                    if isinstance(od_res, dict) and "labels" in od_res:
                        for label in od_res["labels"]:
                            clean_label = str(label).strip().lower()
                            if clean_label and "person" not in clean_label and clean_label not in obj_list:
                                obj_list.append(clean_label)
                    objects_batch[idx] = obj_list
            except Exception as e:
                print(f"      ⚠️ Florence-2 다중 배치 처리 중 오류: {e}")

        # --- [C] EXIF 메타데이터 다중 배치 추출 (폴더명 파싱 완전 배제) ---
        batch_filepaths = [item["filepath"] for item in valid_items]
        exif_dict = {}
        try:
            import subprocess, json
            cmd = ["exiftool", "-j", "-c", "%+.6f", "-DateTimeOriginal", "-CreateDate", "-Location", "-XMP:Location", "-GPSLatitude", "-GPSLongitude"] + batch_filepaths
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                # exiftool JSON 출력 파싱
                parsed_list = json.loads(res.stdout)
                for f_data in parsed_list:
                    # exiftool returns SourceFile keys with normalized paths
                    fpath = f_data.get("SourceFile", "")
                    fname = os.path.basename(fpath)
                    
                    date_val = f_data.get('DateTimeOriginal') or f_data.get('CreateDate')
                    dt_str = "Unknown Date"
                    if date_val:
                        raw_dt = str(date_val).split(' ')[0]
                        parts = raw_dt.split(':')
                        if len(parts) >= 2:
                            dt_str = f"{parts[0]}-{parts[1]}"
                        else:
                            dt_str = raw_dt.replace(':', '-')
                            
                    loc_str = "Unknown Location" # XMP Location 완전 폐기, 항상 GPS 우선 역추적

                    
                    lat_f = None
                    lon_f = None
                    try:
                        lat_raw = f_data.get('GPSLatitude')
                        lon_raw = f_data.get('GPSLongitude')
                        if lat_raw and lon_raw:
                            lat_f = float(str(lat_raw).replace('+', ''))
                            lon_f = float(str(lon_raw).replace('+', ''))
                    except: pass
                    
                    exif_dict[fname] = {"date": dt_str, "loc": loc_str, "lat": lat_f, "lon": lon_f}
        except Exception as e:
            print(f"      🚨 배치 EXIF 추출 오류: {e}")

        # --- DB Upsert 조립 ---
        for i, item in enumerate(valid_items):
            try:
                filepath = item["filepath"]
                cv_img = item["cv_img"]
                point_id = item["point_id"]
                scene_embedding = scene_embeddings[i] if scene_embeddings[i] is not None else np.zeros(768)
                scene_caption = captions_batch[i]
                found_objects = objects_batch[i]
                
                face_count = 0
                found_people = ["No People"]
                best_face_payload = {}
                vectors = {"scene": scene_embedding.tolist()}
                
                if self.insightface:
                    face_res = self.insightface.analyze_image(filepath, cv_img=cv_img)
                    face_count = face_res["face_count"]
                    found_people = face_res["found_people"]
                    best_face_payload = face_res["payload"]
                    if "face" in face_res["vectors"]:
                        vectors["face"] = face_res["vectors"]["face"]
                    for obj in face_res["objects"]:
                        if obj not in found_objects:
                            found_objects.append(obj)
                else:
                    # When skip_face is True (Feedback mode), keep existing face data from DB
                    # We will NOT overwrite it here because Qdrant's upsert replaces the payload.
                    # Wait, if we upsert, we might wipe out the missing face info.
                    # Use Qdrant retrieve to fetch existing face info if we are just re-indexing for location!
                    try:
                        pts = self.q_client.retrieve(COLLECTION_NAME, ids=[point_id], with_payload=True, with_vectors=True)
                        if pts:
                            pt = pts[0]
                            old_p = pt.payload or {}
                            face_count = old_p.get("face_count", 0)
                            found_people = old_p.get("people", ["No People"])
                            best_face_payload = {
                                "age": old_p.get("age"),
                                "gender": old_p.get("gender"),
                                "emotion": old_p.get("emotion")
                            }
                            if "face_bbox" in old_p:
                                best_face_payload["face_bbox"] = old_p["face_bbox"]
                            if pt.vector and "face" in pt.vector:
                                vectors["face"] = pt.vector["face"]
                    except: pass

                # EXIF 기반 데이터 매칭 (폴더명 기반 강제 규정 로직 완벽 제거)
                date_str = "Unknown Date"
                location_str = "Unknown Location"
                lat_f = None
                lon_f = None
                
                fname = os.path.basename(filepath)
                if fname in exif_dict:
                    date_str = exif_dict[fname]["date"]
                    location_str = exif_dict[fname]["loc"]
                    lat_f = exif_dict[fname]["lat"]
                    lon_f = exif_dict[fname]["lon"]
                        
                if force_location and "Unknown" not in force_location:
                    location_str = force_location
                if force_date and "Unknown" not in force_date:
                    date_str = force_date
                    
                # [ OSM 글로벌 지능형 위치 번역 캐시 시스템 ]
                if lat_f is not None and lon_f is not None and location_str == "Unknown Location":
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
                                    import json
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
                                        
                                    
                                    import unicodedata
                                    def _remove_latin(t):
                                        if not isinstance(t, str): return t
                                        res = ""
                                        for c in t:
                                            if 'LATIN' in unicodedata.name(c, ''):
                                                res += unicodedata.normalize('NFD', c).encode('ascii', 'ignore').decode('utf-8')
                                            else: res += c
                                        return res
                                        
                                    location_str = _remove_latin(self.location_cache[cache_key])
                                    print(f"      [📍 OSM 스마트 번역 성공] {lat_key}_{lon_key} ➡️ {location_str}")
                        except Exception as gc_e:
                            print(f"      [-] OSM 역 지오코딩 에러: {gc_e}")
                            self.location_cache[cache_key] = "Unknown Location"
                            
                # [ WebP 프론트엔드 최적화 썸네일 자동 생성 ]
                try:
                    from PIL import Image, ImageOps
                    orig_ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ""
                    base_name = os.path.splitext(filepath)[0]
                    thumb_path = f"{base_name}_{orig_ext}.webp"
                    if not os.path.exists(thumb_path):
                        with Image.open(filepath) as t_img:
                            t_img = ImageOps.exif_transpose(t_img)
                            t_img.thumbnail((300, 300))
                            if t_img.mode in ("RGBA", "P"): t_img = t_img.convert("RGB")
                            t_img.save(thumb_path, "WEBP", quality=75)
                except Exception as t_e:
                    print(f"      [-] WebP 썸네일 생성 실패: {t_e}")
                    
                sort_date = 0
                if date_str != "Unknown Date":
                    import re
                    match_sd = re.search(r'(19|20)\d{2}(-\d{2})?(-\d{2})?', date_str)
                    if match_sd:
                        sd_parts = match_sd.group(0).split('-')
                        while len(sd_parts) < 3:
                            sd_parts.append("01")
                        sort_date = int(sd_parts[0]) * 10000 + int(sd_parts[1]) * 100 + int(sd_parts[2])
                if sort_date == 0:
                    try:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                        sort_date = dt.year * 10000 + dt.month * 100 + dt.day
                    except Exception:
                        sort_date = 0
                print(f"DEBUG: {filepath} => date_str: {date_str}, sort_date: {sort_date}")
                        
                if self.run_vision_ai or self.run_semantic_ai or not self.skip_face:
                    payload = {
                        "filepath": filepath,
                        "filename": item["filename"],
                        "original_context": item["context_str"],
                        "face_count": face_count,
                        "people": found_people,
                        "date": date_str,
                        "sort_date": sort_date,
                        "location": location_str,
                        "season": item["season"],
                        "objects": found_objects,
                        "caption": scene_caption,
                        "hash": item["file_hash"]
                    }
                    payload.update(best_face_payload)
                    successful_payloads.append((filepath, payload, face_count))
                    points_to_upsert.append(PointStruct(id=point_id, vector=vectors, payload=payload))
                elif self.run_metadata_geo:
                    update_payload = {"location": location_str, "date": date_str, "sort_date": sort_date, "season": item["season"]}
                    self.q_client.set_payload(collection_name=COLLECTION_NAME, payload=update_payload, points=[point_id])
                    successful_payloads.append((filepath, update_payload, face_count))
                    
            except Exception as e:
                print(f"      ⚠️ 개별 항목 payload 병합 오류 (Skip): {e}")
                self.failed_filepaths.add(filepath)
                
        # [모드 분기] Qdrant 일괄 묶음 사격
        if points_to_upsert:
            try:
                self.q_client.upsert(collection_name=COLLECTION_NAME, points=points_to_upsert)
                
                # 성공적으로 Qdrant에 저장된 사진들만 원자성(Atomicity)을 보장하며 메모리 캐시 갱신 (SQLite 완전 탈피)
                for filepath, payload, face_count in successful_payloads:
                    self.indexed_filepaths.add(filepath)
                
            except Exception as qdrant_err:
                print(f"    🚨 Qdrant 배치 업서트 치명적 실패: {qdrant_err}")
            
        # VRAM 메모리 단편화 및 좀비 텐서를 해제하여 장시간 가동 시의 쿠다 OOM 다운 방어
        torch.cuda.empty_cache()
        gc.collect()

    def force_reindex_files(self, target_filepaths, force_location=None, force_date=None):
        print(f"[*] 강제 리인덱싱(덮어쓰기) 모드 발동: {len(target_filepaths)}장")
        for i in range(0, len(target_filepaths), BATCH_SIZE):
            chunk = target_filepaths[i:i + BATCH_SIZE]
            batch = []
            for filepath in chunk:
                if not os.path.exists(filepath):
                    continue
                try:
                    pil_img = Image.open(filepath).convert('RGB')
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    context_str = self.get_original_context(filepath)
                    time_of_day, season = self.extract_time_and_season(filepath)
                    import uuid
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
                    batch.append({
                        "filepath": filepath,
                        "filename": os.path.basename(filepath),
                        "pil_img": pil_img,
                        "cv_img": cv_img,
                        "context_str": context_str,
                        "time_of_day": time_of_day,
                        "season": season,
                        "point_id": point_id,
                        "file_hash": self.get_file_hash(filepath)
                    })
                except Exception as e:
                    print(f"  [-] {filepath} 강제 분석 실패: {e}")
            
            if batch:
                self.process_batch(batch, force_location=force_location, force_date=force_date)
        print("[+] 메타데이터 덮어쓰기 완료!")

    def run(self, test_limit=None):
        print("\n🚀 [3단계: 딥러닝 벡터화 파이프라인 가동]")
        # 1. 1단계에서 정리되어 들어온 OrganizedPhotos (app/data/organized) 내의 모든 이미지 스캔
        all_targets = []
        for root, dirs, files in os.walk(TARGET_DIR):
            # 절대 스캔하면 안 되는 원본/격리/테스트 폴더 목록 (하위 탐색 자체를 차단)
            blacklist = ['OriginalSource', 'junk_screenshots', 'b_cuts', 'test_images', '.git', 'uploads_raw', 'enrolled', 'test', 'unknown']
            dirs[:] = [d for d in dirs if d not in blacklist]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                    all_targets.append(os.path.join(root, file))
                    
        # --- [테스트 모드용 로직] ---
        if test_limit:
            import random
            random.shuffle(all_targets)
            all_targets = all_targets[:test_limit]
            print(f"[*] ⚠️ 테스트 모드가 활성화되었습니다. 무작위 {test_limit}장만 스캔합니다.")
            
        total = len(all_targets)
        print(f"[*] 총 {total}장의 대상 사진을 발견했습니다. (동영상 제외)")
        
        # 2. CPU + GPU 멀티스레딩 파이프라인 (Producer-Consumer)
        import threading
        import queue
        import concurrent.futures

        batch_queue = queue.Queue(maxsize=1) # 메모리 버퍼: 너무 많으면 RAM OOM 발생! 최대 1개 선로딩

        def cpu_producer():
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                for i in range(0, total, BATCH_SIZE):
                    batch_paths = all_targets[i : i + BATCH_SIZE]
                    
                    def prep(filepath):
                        # DB Check 
                        if self.is_already_processed(filepath):
                            return None
                        
                        try:
                            # 디스크 병목 구역 (멀티스레딩 효과 극대화)
                            pil_img = Image.open(filepath).convert('RGB')
                            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                            context_str = self.get_original_context(filepath)
                            time_of_day, season = self.extract_time_and_season(filepath)
                            import uuid
                            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
                            
                            return {
                                "filepath": filepath,
                                "filename": os.path.basename(filepath),
                                "pil_img": pil_img,
                                "cv_img": cv_img,
                                "context_str": context_str,
                                "time_of_day": time_of_day,
                                "season": season,
                                "point_id": point_id,
                                "file_hash": self.get_file_hash(filepath)
                            }
                        except Exception as e:
                            print(f"      ⚠️ 이미지 로드 오류 (Skip): {os.path.basename(filepath)} - {e}")
                            self.failed_filepaths.add(filepath)
                            return None
                            
                    results = list(executor.map(prep, batch_paths))
                    valid_items = [r for r in results if r is not None]
                    batch_queue.put((i, valid_items))
                    
            batch_queue.put(None) # 작업 종료 마커
            
        prod_thread = threading.Thread(target=cpu_producer)
        prod_thread.start()
        
        while True:
            item = batch_queue.get()
            if item is None:
                break
            i, valid_items = item
            print(f"\n[*] 📦 배치 진행 중 (CPU+GPU 풀가동): {i+1} ~ {min(i+BATCH_SIZE, total)} / {total}")
            self.process_batch(valid_items)
            
        prod_thread.join()
            
        print("\n✅ 모든 사진의 [얼굴 + 배경 상황] 벡터 데이터베이스 컴파일이 완료되었습니다!")

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='GumaPhoto Vector Indexer')
    parser.add_argument('--test', type=int, help='테스트 모드: 지정된 갯수만큼만 무작위 스캔', default=None)
    parser.add_argument('--update-location', action='store_true', help='[장소만 갱신]: 모든 AI를 차단하고 오직 GPS 번역만 재수행합니다.')
    parser.add_argument('--skip-ai', action='store_true', help='[모든 AI 차단]: 메타데이터/WebP만 갱신합니다.')
    
    args = parser.parse_args()
    
    if args.update_location or args.skip_ai:
        print("\n🚀 [모드 전환] 초경량 업데이트 스위치가 켜졌습니다. VRAM을 소모하지 않습니다.")
        indexer = VectorIndexer(
            run_vision_ai=False,
            run_semantic_ai=False,
            run_facial_ai=False,
            run_metadata_geo=True,
            run_webp_thumbnail=not args.update_location # 장소 업데이트 시 썸네일 불필요
        )
    else:
        indexer = VectorIndexer()
        
    if args.test:
        indexer.run(test_limit=args.test)
    else:
        indexer.run()
