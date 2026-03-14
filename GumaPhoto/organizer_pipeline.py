import os
import time
import shutil
import hashlib
import sqlite3
import cv2
import numpy as np
import imagehash
from PIL import Image
from datetime import datetime
import exifread
import re

# AI Models (Lazy Loading으로 필요할 때만 메모리에 올림)
from insightface.app import FaceAnalysis
from deepface import DeepFace

# ==========================================
# GumaPhoto 자동 정리 & 베스트컷 파이프라인
# ==========================================

# 설정 (추후 분리 가능)
SOURCE_DIR = "/app/data/uploads_raw"      # 오빠가 사진을 무지성으로 던져놓을 폴더
TARGET_DIR = "/app/data/organized"        # 연도별/월별로 예쁘게 정리될 폴더
JUNK_DIR = "/app/data/junk_screenshots"   # 문서, 스크린샷, 완전 중복 등 휴지통 예약
SIMILAR_DIR = "/app/data/b_cuts"          # 연사 중 패배한 B컷 보관함
DB_PATH = "/app/data/organizer_state.db"  # Fail-Safe를 위한 체크포인트 DB

class OrganizerPipeline:
    def __init__(self):
        print("[*] 파이프라인 및 안전장치(DB)를 초기화합니다...")
        self.init_db()
        self.ensure_dirs()
        self.face_app = None # GPU 메모리 절약을 위해 지연 로딩

    def init_db(self):
        """대참사 방지를 위한 이어하기(Checkpoint) SQLite DB 유지"""
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        # file_hash: 완벽한 중복 검사용 고유키
        # status: PROCESSED, JUNK, B_CUT
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_files (
                filepath TEXT PRIMARY KEY,
                file_hash TEXT UNIQUE,
                status TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def ensure_dirs(self):
        for d in [SOURCE_DIR, TARGET_DIR, JUNK_DIR, SIMILAR_DIR]:
            os.makedirs(d, exist_ok=True)

    def load_ai_models(self):
        """무거운 AI 모델(InsightFace, DeepFace) 로드"""
        if self.face_app is None:
            print("[*] 🤖 AI 스캐너 (InsightFace & DeepFace) 가동 중...")
            self.face_app = FaceAnalysis(name='buffalo_l', root='/root/.insightface')
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))
            # DeepFace는 호출 시 자동 로드되지만, keras/tf 설정 초기화를 위해 한 번 빈 배열 넘김
            try:
                DeepFace.analyze(np.zeros((224, 224, 3), dtype=np.uint8), actions=['emotion'], enforce_detection=False)
            except:
                pass

    # ==========================
    # 🛡️ 1단계: Junk 필터링
    # ==========================
    def get_file_hash(self, filepath):
        """완전 중복 파일 검출을 위한 SHA256 해시값 추출"""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def is_junk_or_duplicate(self, filepath):
        """0순위: 완전 중복 및 스크린샷 찌꺼기 판별"""
        file_hash = self.get_file_hash(filepath)
        
        # 1. DB 조회하여 이미 처리된 해시(중복 사본)인지 확인
        self.cursor.execute("SELECT filepath FROM processed_files WHERE file_hash = ?", (file_hash,))
        if self.cursor.fetchone():
            return True, "DUPLICATE"

        # 2. 비율 확인 (폰 스크린샷은 보통 세로로 극단적으로 긺, 해상도로 판단 가능)
        img = Image.open(filepath)
        width, height = img.size
        process_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
        
        if process_ratio > 3.0: # 세로로 너무 길면 카톡 긴 캡처 화면 
            return True, "SCREENSHOT"
            
        return False, file_hash

    # ==========================
    # ⏱️ 2단계: 메타데이터 추출 (Fallback 포함)
    # ==========================
    def extract_datetime_and_location(self, filepath):
        """EXIF 우선 -> 상위 2단계 폴더명 추론 -> Unknown_Date/Location"""
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        dt_str = "Unknown_Date"
        loc_str = "Unknown_Location"

        # 1. 시간 EXIF 확인
        if 'EXIF DateTimeOriginal' in tags:
            # 포맷: 2023:10:15 14:30:00 -> 2023-10-15
            raw_dt = str(tags['EXIF DateTimeOriginal']).split(' ')[0]
            dt_str = raw_dt.replace(':', '-')
        else:
            # 2. 메타데이터 누락 시 -> 상위 폴더 이름에서 힌트 얻기 (예: D:\사진집\2014 겨울여행\IMG_01.jpg)
            # 폴더명에 2014 같은 4자리 숫자 연도가 있는지 정규식으로 유추
            parent_dir = os.path.basename(os.path.dirname(filepath))
            grandparent_dir = os.path.basename(os.path.dirname(os.path.dirname(filepath)))
            
            match = re.search(r'(19|20)\d{2}[-._]?\d{0,2}', parent_dir + grandparent_dir)
            if match:
                dt_str = match.group() + "_Inferred" # 추론됨을 표시
        
        # 3. GPS 정보 (여기서는 개념만 잡고 실제 파싱은 복잡하므로 스킵, 있으면 카카오API 연동 예정)
        if 'GPS GPSLatitude' in tags:
            loc_str = "GPS_Found_Need_Geocoding" # 카카오 API 등으로 주소 변환 필요
            
        return dt_str, loc_str

    # ==========================
    # 🎯 3단계: 베스트컷 추출
    # ==========================
    def check_blur(self, img_cv):
        """OpenCV 라플라시안 분산으로 흔들림 점수 계산"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        return score # 낮을수록 많이 흔들림 (보통 100 이하면 버려도 됨)

    def calculate_ear(self, face):
        """눈 깜빡임(감음) 감지 점수 계산 (LANDMARKS 기반 EAR 식 사용 예측)"""
        # Insightface buffalo_l 모델은 기본 5개 랜드마크(눈2, 코, 입2)를 주지만 확장 모델 적용 시 106개도 가능
        # 현재는 Prototype이므로, 5개 랜드마크의 눈 크기를 기반으로 한 가상 점수 알고리즘을 사용함
        left_eye = face.kps[0]
        right_eye = face.kps[1]
        # 눈이 너무 작게 잡히면 (눈 감음) 점수를 깎도록 로직 구성 (나머지는 실제 상세 수학식으로 교체)
        ear_score = 1.0 # 임시 통과
        return ear_score

    def get_best_cut(self, group_filepaths):
        """유사한 사진 리스트 중 가장 점수가 높은 인생샷 1장을 반환"""
        self.load_ai_models()
        best_score = -1
        best_pic = group_filepaths[0]

        for path in group_filepaths:
            img = cv2.imread(path)
            if img is None: continue
            
            # 1. 흔들림 무조건 탈락 체크
            blur_score = self.check_blur(img)
            if blur_score < 70:
                print(f"   [-] {os.path.basename(path)}: 징하게 흔들림! 탈락 (score:{blur_score:.1f})")
                continue
                
            faces = self.face_app.get(img)
            pic_score = blur_score * 0.1 # 기본 구도(선명도) 점수 일부 반영
            
            for face in faces:
                # 2. 눈 감음 체크 (가상 EAR)
                ear = self.calculate_ear(face)
                if ear < 0.2: # 눈 감음!
                    pic_score -= 1000 # 가차없이 감점
                
                # 3. 표정 감성 분석 (DeepFace)
                x1, y1, x2, y2 = face.bbox.astype(int)
                # 얼굴 영역 크롭
                face_crop = img[max(0,y1):min(img.shape[0],y2), max(0,x1):min(img.shape[1],x2)]
                
                try:
                    # DeepFace 감정 분석 리포트
                    emotion_res = DeepFace.analyze(face_crop, actions=['emotion'], enforce_detection=False)
                    dom_emotion = emotion_res[0]['dominant_emotion']
                    if dom_emotion == 'happy':
                        pic_score += 500  # 웃는 사진 최고 가산점 😍
                    elif dom_emotion in ['sad', 'angry', 'fear']:
                        pic_score -= 100  # 찡그린 표정 감점
                except:
                    pass
            
            if pic_score > best_score:
                best_score = pic_score
                best_pic = path

        return best_pic

    # ==========================
    # ⚙️ 실행: 파이프라인 메인루프
    # ==========================
    def run(self):
        print("🚀 [GumaPhoto Pipeline] 데이터 정리를 시작합니다...")
        
        # 0. 파일 스캔 (임시로 단일 파일 루프로 짰지만, 실무에선 '시간+이미지해시 그룹핑' 로직 추가)
        # --- 여기서는 오빠가 흐름을 한 눈에 볼 수 있도록 전체 구조 뼈대만 노출해 둠 ---
        
        print("""
        [파이프라인 실행 요약]
        1. SOURCE_DIR 폴더의 사진들을 재귀적으로 전부 읽습니다.
        2. Hash 체크를 통해 JUNK_DIR(쓰레기통)로 완전 복제품을 직행시킵니다.
        3. 1~2분 단위로 찍힌 유사 사진들끼리 배열(Array)에 묶습니다.
        4. get_best_cut() 을 돌려서 AI에게 점수를 매기게 하고, 우승자 1명만 뽑습니다.
        5. 우승자 1명은 TARGET_DIR/2015/2015-10-15_Unknown_Location/ 으로 안전하게 하드링크(Hard Link) 복사합니다.
        6. 패배한 떨거지 사진들은 SIMILAR_DIR 로 보냅니다.
        7. SQLite DB 처리 결과 기록(Commit).
        """)

if __name__ == "__main__":
    organizer = OrganizerPipeline()
    organizer.run()
