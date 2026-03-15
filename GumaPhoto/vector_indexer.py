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
BATCH_SIZE = 50 # 한 번에 처리할 사진 수 (GPU 메모리 고려)

class VectorIndexer:
    def __init__(self):
        print(f"[*] 벡터 DB (Qdrant) 접속 초기화... ({QDRANT_URL})")
        self.q_client = QdrantClient(url=QDRANT_URL)
        self.init_qdrant_collection()
        
        print("[*] SQLite (상태 관리용 DB) 접속 초기화...")
        self.conn = sqlite3.connect(DB_PATH, timeout=60)
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
        self.emotion_recognizer = HSEmotionRecognizer(model_name='enet_b0_8_best_vgaf', device=device)
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
        self.cursor.execute("SELECT original_context FROM processed_files WHERE file_hash=?", (file_hash,))
        row = self.cursor.fetchone()
        return row[0] if row else "Organized_Photo"

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
        self.cursor.execute("SELECT status FROM vectorized_files WHERE filepath=?", (filepath,))
        row = self.cursor.fetchone()
        return row and row[0] == 'DONE'

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

    def process_batch(self, file_batch):
        """배치(묶음) 단위로 10~50장의 사진을 메모리에 올려 병렬로 처리함"""
        points_to_upsert = []
        
        for filepath in file_batch:
            if self.is_already_processed(filepath):
                continue
                
            print(f"   [벡터화] 스캔 중: {os.path.basename(filepath)}")
            try:
                # 1. 파일의 해시값을 계산하여 최초 1단계 Organizer에서 저장한 원본 DB 기록 조회
                file_hash = self.get_file_hash(filepath)
                context_str = self.get_original_context(file_hash)
                
                # 추가 컨텍스트 추출 (시간대, 계절)
                time_of_day, season = self.extract_time_and_season(filepath)
                
                # --- [A] SigLIP 픽셀 백터 (Scene) 추출 ---
                pil_img = Image.open(filepath).convert('RGB')
                siglip_inputs = self.siglip_processor(images=pil_img, return_tensors="pt").to(self.siglip_model.device)
                with torch.no_grad():
                    out = self.siglip_model.get_image_features(**siglip_inputs)
                    if hasattr(out, "pooler_output"):
                        emb = out.pooler_output[0]
                    elif hasattr(out, "shape"):
                        emb = out[0]
                    else:
                        emb = out[0]
                    emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
                    scene_embedding = emb.cpu().numpy()
                
                # --- [B] InsightFace (Face) 추출 ---
                # 주의: InsightFace는 BGR(OpenCV 포맷) 이미지를 요구함
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                faces = self.face_app.get(cv_img)
                
                face_count = len(faces)
                
                # Qdrant 고유 ID는 문자열 해시나 유니크 정수가 필요 (여기선 파일경로 해시로 대체)
                import uuid
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
                
                # --- [C] 다중 벡터(MultiVector) 조립 ---
                vectors = {
                    "scene": scene_embedding.tolist()
                }
                
                # 얼굴이 감지되었다면, 그중 가장 면적이 큰(메인 인물) 1명의 얼굴 벡터만 대표로 저장 (또는 컬렉션 구조에 따라 배열로 분리)
                # (Qdrant는 Point 1개당 'face' 벡터를 1개만 받을 수 있으므로, 다수의 얼굴이면 개별 Point로 쪼개야 함. 여기서는 심플하게 1등 얼굴만 채택)
                best_face_payload = {}
                found_people = []
                
                if face_count > 0:
                    # 모든 감지된 얼굴에 대해 known_faces와 비교하여 인물 태그 추출
                    for face in faces:
                        norm_emb = face.normed_embedding
                        best_match_name = None
                        best_sim = 0.40 # 코사인 유사도 커트라인
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
                    
                    # --- [InsightFace -> Family Meta : 나이/성별 보정 적용] ---
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
                        
                        import re
                        match = re.search(r'(19|20)\d{2}', filepath)
                        if born_year and match:
                            photo_year = int(match.group(0))
                            real_age = photo_year - born_year
                            
                    best_face_payload['age'] = real_age
                    best_face_payload['gender'] = real_gender
                    
                    # --- [HSEmotion: 표정 분석] ---
                    box = best_face.bbox.astype(int)
                    x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(cv_img.shape[1], box[2]), min(cv_img.shape[0], box[3])
                    face_img = cv_img[y1:y2, x1:x2]
                    
                    try:
                        if face_img.size > 0:
                            emotion, scores = self.emotion_recognizer.predict_emotions(face_img, logits=False)
                            best_face_payload['emotion'] = emotion
                        else:
                            best_face_payload['emotion'] = 'neutral'
                    except Exception as df_e:
                        print(f"      ⚠️ HSEmotion 분석 실패 (Skip): {df_e}")
                        best_face_payload['emotion'] = 'neutral'
                else:
                    found_people.append("No People")
                    
                # --- [Florence-2: 고급 문맥 묘사(Caption) 추출 및 사물(OD) 태깅] ---
                scene_caption = ""
                found_objects = []
                if getattr(self, "florence_model", None):
                    try:
                        # 1. 캡션 추출
                        task_prompt_cap = "<MORE_DETAILED_CAPTION>"
                        flo_inputs_cap = self.florence_processor(text=task_prompt_cap, images=pil_img, return_tensors="pt").to(self.florence_model.device)
                        with torch.no_grad():
                            generated_ids_cap = self.florence_model.generate(
                                input_ids=flo_inputs_cap["input_ids"],
                                pixel_values=flo_inputs_cap["pixel_values"],
                                max_new_tokens=512,
                                early_stopping=False,
                                do_sample=False,
                                num_beams=1,
                            )
                        generated_text_cap = self.florence_processor.batch_decode(generated_ids_cap, skip_special_tokens=False)[0]
                        parsed_answer_cap = self.florence_processor.post_process_generation(
                            generated_text_cap, 
                            task=task_prompt_cap, 
                            image_size=(pil_img.width, pil_img.height)
                        )
                        scene_caption = parsed_answer_cap.get(task_prompt_cap, "")
                        
                        # 2. 사물 태그(Object Detection) 추출
                        task_prompt_od = "<OD>"
                        flo_inputs_od = self.florence_processor(text=task_prompt_od, images=pil_img, return_tensors="pt").to(self.florence_model.device)
                        with torch.no_grad():
                            generated_ids_od = self.florence_model.generate(
                                input_ids=flo_inputs_od["input_ids"],
                                pixel_values=flo_inputs_od["pixel_values"],
                                max_new_tokens=1024,
                                early_stopping=False,
                                do_sample=False,
                                num_beams=1,
                            )
                        generated_text_od = self.florence_processor.batch_decode(generated_ids_od, skip_special_tokens=False)[0]
                        parsed_answer_od = self.florence_processor.post_process_generation(
                            generated_text_od, 
                            task=task_prompt_od, 
                            image_size=(pil_img.width, pil_img.height)
                        )
                        od_results = parsed_answer_od.get(task_prompt_od, {})
                        if isinstance(od_results, dict) and "labels" in od_results:
                            for label in od_results["labels"]:
                                # 소문자화 및 공백 제거
                                clean_label = str(label).strip().lower()
                                # 빈 문자열이나 "person"은 스킵
                                if clean_label and "person" not in clean_label and clean_label not in found_objects:
                                    found_objects.append(clean_label)
                                    
                    except Exception as flo_e:
                        print(f"      ⚠️ Florence-2 분석 실패 (Skip): {flo_e}")
                        
                # --- [날짜(Date) 및 위치(Location) 파싱] ---
                # 경로 형식: /app/data/organized/2020/2020-10_Jecheon-Si-South-Korea/2020-10_63.jpg
                parent_dir = os.path.basename(os.path.dirname(filepath))
                location_str = "Unknown Location"
                date_str = "Unknown Date"
                
                if "_" in parent_dir:
                    parts = parent_dir.split("_", 1)
                    
                    # 1. 2020-10 연월 단위 날짜 추출
                    if re.match(r'^(19|20)\d{2}', parts[0]):
                        date_str = parts[0]
                        
                    # 2. 장소/위치명 추출
                    if len(parts) > 1 and parts[1] != "Unknown-Location" and parts[1] != "Unknown-Year":
                        location_str = parts[1].replace("-", " ")
                    
                # --- [D] Payload 조립 및 저장 ---
                payload = {
                    "filepath": filepath,
                    "filename": os.path.basename(filepath),
                    "original_context": context_str,
                    "face_count": face_count,
                    "people": found_people,
                    "date": date_str,
                    "location": location_str,
                    "time_of_day": time_of_day,
                    "season": season,
                    "objects": found_objects,
                    "caption": scene_caption
                }
                payload.update(best_face_payload)
                
                points_to_upsert.append(PointStruct(id=point_id, vector=vectors, payload=payload))
                
                # SQLite 진행도 마킹
                self.cursor.execute("INSERT OR REPLACE INTO vectorized_files (filepath, status, face_count) VALUES (?, ?, ?)",
                                  (filepath, 'DONE', face_count))
                
            except Exception as e:
                print(f"      ⚠️ 오류 발생 (Skip): {e}")
                self.cursor.execute("INSERT OR REPLACE INTO vectorized_files (filepath, status) VALUES (?, ?)", (filepath, 'ERROR'))
                
        # Qdrant에 일괄 묶음 사격 (배치 Upsert)
        if points_to_upsert:
            self.q_client.upsert(collection_name=COLLECTION_NAME, points=points_to_upsert)
            self.conn.commit()
            
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
                if ext in ['.jpg', '.jpeg', '.png']:
                    all_targets.append(os.path.join(root, file))
                    
        # --- [테스트 모드용 로직] ---
        if test_limit:
            import random
            random.shuffle(all_targets)
            all_targets = all_targets[:test_limit]
            print(f"[*] ⚠️ 테스트 모드가 활성화되었습니다. 무작위 {test_limit}장만 스캔합니다.")
            
        total = len(all_targets)
        print(f"[*] 총 {total}장의 대상 사진을 발견했습니다. (동영상 제외)")
        
        # 2. BATCH_SIZE 묶음 단위로 끊어서 진행
        for i in range(0, total, BATCH_SIZE):
            batch = all_targets[i : i + BATCH_SIZE]
            print(f"\n[*] 📦 배치 처리 중: {i+1} ~ {i+len(batch)} / {total}")
            self.process_batch(batch)
            
        print("\n✅ 모든 사진의 [얼굴 + 배경 상황] 벡터 데이터베이스 컴파일이 완료되었습니다!")

if __name__ == "__main__":
    import sys
    indexer = VectorIndexer()
    
    # python vector_indexer.py --test 20 형태로 실행 가능하게 설정
    if len(sys.argv) == 3 and sys.argv[1] == '--test':
        indexer.run(test_limit=int(sys.argv[2]))
    else:
        indexer.run()
