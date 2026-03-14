import os
import sqlite3
import numpy as np
import cv2
import time
import hashlib
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from insightface.app import FaceAnalysis
from deepface import DeepFace

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
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self.init_sqlite_tables()
        
        self.load_ai_models()

    def init_qdrant_collection(self):
        """다중 벡터(Multivector)를 수용할 수 있는 Qdrant 컬렉션 뼈대 생성"""
        # Qdrant v1.1.0 이상부터 Named Vectors 기능을 지원하여 한 Point 내에 여러 목적의 벡터 저장 가능
        if not self.q_client.collection_exists(collection_name=COLLECTION_NAME):
            self.q_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "scene": VectorParams(size=512, distance=Distance.COSINE),
                    "face": VectorParams(size=512, distance=Distance.COSINE)
                }
            )
            # 메타데이터 검색 속도 최적화를 위한 페이로드 인덱스 생성
            self.q_client.create_payload_index(COLLECTION_NAME, "original_context", "text")
            self.q_client.create_payload_index(COLLECTION_NAME, "filepath", "keyword")
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
        """🚀 CLIP (배경/상황) & InsightFace (얼굴) 모델 VRAM 로드"""
        print("[*] 🖼️ 일반 CLIP 이미지 인코더 로드 중 (clip-ViT-B-32) ...")
        # 참고: multilingual-v1 모델은 텍스트 검색(Search) 시에만 사용하며, 사진 자체를 변환할 땐 오리지널 CLIP을 사용해야 차원(Vector Space)이 일치함
        self.clip_model = SentenceTransformer('clip-ViT-B-32')
        
        print("[*] 👤 InsightFace 얼굴 인식 모델 로드 중 (buffalo_l) ...")
        # GPU 가용 시 CUDA 사용, 아니면 CPU 동작 (providers에서 지정)
        self.face_app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        print("  [+] 모든 초거대 AI 모델 로딩 완료!")

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
                
                # --- [A] CLIP 픽셀 백터 (Scene) 추출 ---
                pil_img = Image.open(filepath).convert('RGB')
                scene_embedding = self.clip_model.encode(pil_img)
                
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
                if face_count > 0:
                    best_face = sorted(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)[0]
                    vectors["face"] = best_face.normed_embedding.tolist()
                    
                    # --- [DeepFace: 추가 표정/나이/성별 분석] ---
                    box = best_face.bbox.astype(int)
                    x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(cv_img.shape[1], box[2]), min(cv_img.shape[0], box[3])
                    cropped_face = cv_img[y1:y2, x1:x2]
                    
                    try:
                        # DeepFace.analyze를 통해 해당 얼굴 이미지 크롭본 분석 (enforce_detection=False로 안전장치)
                        df_res = DeepFace.analyze(img_path=cropped_face, actions=['age', 'gender', 'emotion'], enforce_detection=False, silent=True)
                        if isinstance(df_res, list):
                            df_res = df_res[0]
                        
                        best_face_payload['age'] = df_res.get('age', 0)
                        best_face_payload['emotion'] = df_res.get('dominant_emotion', 'neutral')
                        
                        gender_data = df_res.get('gender', {})
                        if isinstance(gender_data, dict):
                            best_face_payload['gender'] = max(gender_data, key=gender_data.get)
                        else:
                            best_face_payload['gender'] = str(gender_data)
                            
                    except Exception as df_e:
                        print(f"      ⚠️ DeepFace 분석 실패 (Skip): {df_e}")
                    
                # --- [D] Payload 조립 및 저장 ---
                payload = {
                    "filepath": filepath,
                    "filename": os.path.basename(filepath),
                    "original_context": context_str,
                    "face_count": face_count
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

    def run(self):
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
                    
        total = len(all_targets)
        print(f"[*] 총 {total}장의 대상 사진을 발견했습니다. (동영상 제외)")
        
        # 2. BATCH_SIZE 묶음 단위로 끊어서 진행
        for i in range(0, total, BATCH_SIZE):
            batch = all_targets[i : i + BATCH_SIZE]
            print(f"\n[*] 📦 배치 처리 중: {i+1} ~ {i+len(batch)} / {total}")
            self.process_batch(batch)
            
        print("\n✅ 모든 사진의 [얼굴 + 배경 상황] 벡터 데이터베이스 컴파일이 완료되었습니다!")

if __name__ == "__main__":
    indexer = VectorIndexer()
    indexer.run()
