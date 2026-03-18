import os
import sqlite3
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
DB_PATH = "/app/data/organizer_state.db"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"
BATCH_SIZE = 15 # 한 번에 처리할 사진 수 (GPU, RAM 메모리 고려)

class VectorIndexer:
    def __init__(self):
        print(f"[*] 벡터 DB (Qdrant) 접속 초기화... ({QDRANT_URL})")
        self.q_client = QdrantClient(url=QDRANT_URL, timeout=60)
        self.init_qdrant_collection()
        
        print("[*] SQLite (상태 관리용 DB) 접속 초기화...")
        import threading
        self.db_lock = threading.Lock()
        self.conn = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA journal_mode=DELETE;")
        self.init_sqlite_tables()
        
        self.load_ai_models()

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
            self.q_client.create_payload_index(COLLECTION_NAME, "sort_date", field_schema=PayloadSchemaType.INTEGER)
            print(f"  [+] 신규 Qdrant 멀티-벡터 컬렉션 '{COLLECTION_NAME}' 생성 완료.")
        else:
            print(f"  [-] 기존 Qdrant 컬렉션 '{COLLECTION_NAME}' 을 재사용합니다.")

    def init_sqlite_tables(self):
        """벡터화 진행 상태를 저장하여 도중에 꺼져도 이어하기(Resume) 가능하게 구성"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vectorized_files (
                filepath TEXT PRIMARY KEY,
                status TEXT,
                face_count INTEGER DEFAULT 0,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def load_ai_models(self):
        """🚀 SigLIP (배경/상황) & InsightFace (얼굴) & Florence-2-large 모델 VRAM 로드"""
        print("[*] 🖼️ 초정밀 SigLIP 이미지 인코더 로드 중 (google/siglip-base-patch16-224) ...")
        self.siglip_processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-224")
        self.siglip_model = AutoModel.from_pretrained("google/siglip-base-patch16-224").to('cuda' if torch.cuda.is_available() else 'cpu')
        self.siglip_model.eval()
        
        print("[*] 👤 InsightFace 얼굴 인식 모델 로드 중 (buffalo_l) ...")
        # GPU 가용 시 CUDA 사용, 아니면 CPU 동작 (providers에서 지정)
        self.face_app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        
        print("[*] ❤️ HSEmotion 표정 인식기 로드 중 (enet_b0_8_best_vgaf) ...")
        # PyTorch 2.6 weights_only 오류 방어 패치
        import timm.models.efficientnet
        if hasattr(torch.serialization, 'add_safe_globals'):
            torch.serialization.add_safe_globals([timm.models.efficientnet.EfficientNet])
            try:
                import timm.models.layers.conv2d_same
                torch.serialization.add_safe_globals([timm.models.layers.conv2d_same.Conv2dSame])
            except: pass
        
        _original_load = torch.load
        torch.load = lambda *a, **k: _original_load(*a, weights_only=False, **{key:val for key,val in k.items() if key != 'weights_only'})
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        try:
            self.emotion_recognizer = HSEmotionRecognizer(model_name='enet_b0_8_best_vgaf', device=device)
        except Exception as e:
            print(f"  [!] ⚠️ HSEmotion 모델 다운로드 또는 초기화 실패 (GitHub 429 등): {e}. 감정 인식 기능이 임시 비활성화됩니다.")
            self.emotion_recognizer = None
            
        torch.load = _original_load
        
        # === 가족 메타데이터 로드 ===
        self.known_faces = {}
        if os.path.exists("/app/data/known_faces.pkl"):
            with open("/app/data/known_faces.pkl", "rb") as f:
                raw_faces = pickle.load(f)
                valid_faces = 0
                for name, vectors in raw_faces.items():
                    if vectors:
                        mean_vec = np.mean(vectors, axis=0)
                        mean_vec = mean_vec / np.linalg.norm(mean_vec)
                        self.known_faces[name] = mean_vec
                        valid_faces += 1
            print(f"  [+] 사전에 학습된 가족 얼굴 데이터 {valid_faces}명 로드 완료.")
            
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

    def get_original_context(self, file_hash):
        """1단계에서 저장해둔 원본 문맥(가족_결혼사진 등)을 해시값으로 역추적하여 빼오기"""
        try:
            with getattr(self, "db_lock", __import__("threading").Lock()):
                self.cursor.execute("SELECT original_context FROM processed_files WHERE file_hash=?", (file_hash,))
                row = self.cursor.fetchone()
            return row[0] if row else "Organized_Photo"
        except sqlite3.OperationalError:
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
        """이미 벡터화가 성공적으로 끝난 파일인지 검사 (Fail-safe 이어하기)"""
        import uuid
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
        base_name = os.path.splitext(filepath)[0]
        
        # 0. 빠른 SQLite 조회 (UI 전용 상태)
        try:
            with getattr(self, "db_lock", __import__("threading").Lock()):
                self.cursor.execute("SELECT status FROM vectorized_files WHERE filepath=?", (filepath,))
                row = self.cursor.fetchone()
                if row and row[0] == 'DONE':
                    return True
        except sqlite3.OperationalError:
            pass
            
        # 1. Qdrant 실존 검사
        try:
            records = self.q_client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=[point_id],
                with_payload=False,
                with_vectors=False
            )
            qdrant_has_vector = len(records) > 0
        except Exception:
            qdrant_has_vector = False
            
        # 2. XMP 실존 검사
        xmp_exists = os.path.exists(filepath + ".xmp") or os.path.exists(base_name + ".xmp")
        
        # 완벽 무결성 체크: Qdrant와 XMP가 모두 있으면 SQLite에 벌크로 DONE 채워넣고 패스
        if qdrant_has_vector and xmp_exists:
            try:
                with getattr(self, "db_lock", __import__("threading").Lock()):
                    self.cursor.execute("INSERT OR REPLACE INTO vectorized_files (filepath, status) VALUES (?, ?)", (filepath, 'DONE'))
                    self.conn.commit()
            except sqlite3.OperationalError:
                pass 
            return True
            
        # 둘 중 하나라도 없으면 원자성 실패로 간주, 기존 찌꺼기 싹 지우고 처음부터
        if qdrant_has_vector:
            try:
                from qdrant_client.http.models import PointIdsList
                self.q_client.delete(collection_name=COLLECTION_NAME, points_selector=PointIdsList(points=[point_id]))
            except:
                pass
                
        if xmp_exists:
            try:
                if os.path.exists(filepath + ".xmp"):
                    os.remove(filepath + ".xmp")
                if os.path.exists(base_name + ".xmp"):
                    os.remove(base_name + ".xmp")
            except:
                pass
                
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

    def process_batch(self, valid_items):
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
        try:
            siglip_inputs = self.siglip_processor(images=pil_images, return_tensors="pt").to(self.siglip_model.device)
            with torch.no_grad():
                out = self.siglip_model.get_image_features(**siglip_inputs)
                emb = out / out.norm(p=2, dim=-1, keepdim=True)
                scene_embeddings = emb.cpu().numpy()
        except Exception as e:
            print(f"      🚨 SigLIP 연산 오류: {e}")
            
        # --- [B] Florence-2 다중 배치 추론 ---
        if getattr(self, "florence_model", None):
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

        # --- [C] 개별 연산 (InsightFace) 및 페이로드 조립 ---
        for i, item in enumerate(valid_items):
            try:
                filepath = item["filepath"]
                cv_img = item["cv_img"]
                point_id = item["point_id"]
                scene_embedding = scene_embeddings[i] if scene_embeddings[i] is not None else np.zeros(768)
                scene_caption = captions_batch[i]
                found_objects = objects_batch[i]
                
                faces = self.face_app.get(cv_img)
                face_count = len(faces)
                
                vectors = {"scene": scene_embedding.tolist()}
                best_face_payload = {}
                found_people = []
                
                if face_count > 0:
                    for face in faces:
                        norm_emb = face.normed_embedding
                        best_match_name = None
                        best_sim = 0.40
                        for name, known_vec in self.known_faces.items():
                            sim = np.dot(norm_emb, known_vec)
                            if sim > best_sim:
                                best_sim = sim
                                best_match_name = name
                        if best_match_name and best_match_name not in found_people:
                            found_people.append(best_match_name)
                    
                    if not found_people:
                        found_people.append("Unknown People")

                    best_face = sorted(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)[0]
                    vectors["face"] = best_face.normed_embedding.tolist()
                    
                    ai_age = int(best_face.age)
                    ai_gender = "남성(Male)" if best_face.gender == 1 else "여성(Female)"
                    
                    real_name = "Unknown People"
                    best_sim_main = -1.0
                    for name, k_vec in self.known_faces.items():
                        sim = np.dot(best_face.normed_embedding, k_vec)
                        if sim > best_sim_main:
                            best_sim_main = sim
                            if sim >= 0.35:
                                real_name = name
                                
                    real_age = ai_age
                    real_gender = ai_gender
                    
                    if real_name in self.family_meta:
                        real_gender = self.family_meta[real_name].get("gender", ai_gender)
                        born_year = self.family_meta[real_name].get("birth_year")
                        
                        match = re.search(r'(19|20)\d{2}', filepath)
                        if born_year and match:
                            photo_year = int(match.group(0))
                            real_age = photo_year - born_year
                            
                    best_face_payload['age'] = real_age
                    best_face_payload['gender'] = real_gender
                    
                    age_korean_1 = f"{real_age}세"
                    age_korean_2 = f"{real_age}살"
                    if age_korean_1 not in found_objects: found_objects.append(age_korean_1)
                    if age_korean_2 not in found_objects: found_objects.append(age_korean_2)
                    
                    box = best_face.bbox.astype(int)
                    x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(cv_img.shape[1], box[2]), min(cv_img.shape[0], box[3])
                    face_img = cv_img[y1:y2, x1:x2]
                    
                    try:
                        if face_img.size > 0 and getattr(self, "emotion_recognizer", None):
                            emotion, scores = self.emotion_recognizer.predict_emotions(face_img, logits=False)
                            best_face_payload['emotion'] = emotion
                        else:
                            best_face_payload['emotion'] = 'neutral'
                    except Exception as df_e:
                        print(f"      ⚠️ HSEmotion 분석 실패 (Skip): {df_e}")
                        best_face_payload['emotion'] = 'neutral'
                else:
                    found_people.append("No People")

                parent_dir = os.path.basename(os.path.dirname(filepath))
                location_str = "Unknown Location"
                date_str = "Unknown Date"
                
                if "_" in parent_dir:
                    parts = parent_dir.split("_", 1)
                    if re.match(r'^(19|20)\d{2}', parts[0]):
                        date_str = parts[0]
                    if len(parts) > 1 and parts[1] != "Unknown-Location" and parts[1] != "Unknown-Year":
                        location_str = parts[1].replace("-", " ")
                        
                sort_date = 0
                if date_str != "Unknown Date":
                    match_sd = re.search(r'(19|20)\d{2}(-\d{2})?(-\d{2})?', date_str)
                    if match_sd:
                        sd_full = match_sd.group(0)
                        sd_parts = sd_full.split('-')
                        sd_yr = int(sd_parts[0])
                        sd_mo = int(sd_parts[1]) if len(sd_parts) > 1 else 1
                        sd_dy = int(sd_parts[2]) if len(sd_parts) > 2 else 1
                        sort_date = sd_yr * 10000 + sd_mo * 100 + sd_dy
                if sort_date == 0:
                    try:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                        sort_date = dt.year * 10000 + dt.month * 100 + dt.day
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
                    "caption": scene_caption
                }
                payload.update(best_face_payload)
                
                successful_payloads.append((filepath, payload, face_count))
                points_to_upsert.append(PointStruct(id=point_id, vector=vectors, payload=payload))
                
            except Exception as e:
                print(f"      ⚠️ 개별 항목 payload 병합 오류 (Skip): {e}")
                with getattr(self, "db_lock", __import__("threading").Lock()):
                    self.cursor.execute("INSERT OR REPLACE INTO vectorized_files (filepath, status) VALUES (?, ?)", (filepath, 'ERROR'))
                
        # Qdrant에 일괄 묶음 사격 (배치 Upsert)
        # Qdrant에 일괄 묶음 사격 (배치 Upsert)
        if points_to_upsert:
            try:
                # 1. 가장 중요한 AI 뇌(Qdrant)에 먼저 때려 넣기
                self.q_client.upsert(collection_name=COLLECTION_NAME, points=points_to_upsert)
                
                # 2. XMP 생성 및 SQLite Bulk Insert (성공 시에만)
                import xmp_utils
                db_records = []
                for filepath, payload, face_count in successful_payloads:
                    try:
                        xmp_utils.generate_xmp_sidecar(filepath, payload)
                        db_records.append((filepath, 'DONE', face_count))
                    except Exception as xmp_e:
                        print(f"      ⚠️ XMP 생성 실패: {xmp_e}")
                        db_records.append((filepath, 'ERROR', face_count))
                
                # Bulk DB commit으로 디스크 I/O 최적화
                if db_records:
                    with getattr(self, "db_lock", __import__("threading").Lock()):
                        self.cursor.executemany(
                            "INSERT OR REPLACE INTO vectorized_files (filepath, status, face_count) VALUES (?, ?, ?)",
                            db_records
                        )
                        self.conn.commit()
                        
            except Exception as qdrant_err:
                print(f"    🚨 Qdrant 배치 업서트 치명적 실패: {qdrant_err}")
                # AI DB 기록에 실패했으므로 아무 것도 남기지 않고 다음 번에 처음부터 재시도하도록 냅둠 (Rollback 기조)
            
        # VRAM 메모리 단편화 및 좀비 텐서를 해제하여 장시간 가동 시의 쿠다 OOM 다운 방어
        torch.cuda.empty_cache()
        gc.collect()

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
                if ext in ['.jpg', '.jpeg', '.png', '.heic']:
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
                            file_hash = self.get_file_hash(filepath)
                            context_str = self.get_original_context(file_hash)
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
                                "point_id": point_id
                            }
                        except Exception as e:
                            print(f"      ⚠️ 이미지 로드 오류 (Skip): {os.path.basename(filepath)} - {e}")
                            with getattr(self, "db_lock", __import__("threading").Lock()):
                                self.cursor.execute("INSERT OR REPLACE INTO vectorized_files (filepath, status) VALUES (?, ?)", (filepath, 'ERROR'))
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
    indexer = VectorIndexer()
    
    # python vector_indexer.py --test 20 형태로 실행 가능하게 설정
    if len(sys.argv) == 3 and sys.argv[1] == '--test':
        indexer.run(test_limit=int(sys.argv[2]))
    else:
        indexer.run()
