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
from typing import Any

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
        self.conn: Any = None
        self.cursor: Any = None
        self.face_app: Any = None # GPU 메모리 절약을 위해 지연 로딩
        self.init_db()
        self.ensure_dirs()

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
            
        # --- 🎬 동영상(Video) 처리 바이패스 로직 ---
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.mkv']:
            # 화면 녹화본 찌꺼기 판단 (파일명이나 용량 등 간단한 휴리스틱)
            if 'screenrecording' in os.path.basename(filepath).lower():
                return True, "SCREENRECORDING_VIDEO"
            # 정상적인 동영상 파일이라면 블러/비율 등 이미지 전용 검사를 패스(Bypass)
            return False, file_hash

        # 2. 비율 확인 (폰 스크린샷은 보통 세로로 극단적으로 긺, 해상도로 판단 가능)
        try:
            img = Image.open(filepath)
            width, height = img.size
            # PIL 이미지는 열고 닫는 것이 가벼움
            process_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
            
            if process_ratio > 3.0: # 세로로 너무 길면 카톡 긴 캡처 화면 
                return True, "SCREENSHOT"
        except:
            pass # 이미지 파일이 아니거나 손상된 경우 패스
            
        # 3. 극단적 흔들림(Extreme Blur) 파악 - 심령사진 즉시 제거
        cv_img = cv2.imread(filepath)
        if cv_img is not None:
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score < 15.0: # 15 미만이면 형체를 거의 알아볼 수 없는 수준의 블러
                return True, f"EXTREME_BLUR_SCORE_{blur_score:.1f}"
            
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
            # 포맷: 2023:10:15 14:30:00 -> 2023-10
            raw_dt = str(tags['EXIF DateTimeOriginal']).split(' ')[0]
            # yyyy, mm 두 가지 항목만 붙임
            parts = raw_dt.split(':')
            if len(parts) >= 2:
                dt_str = f"{parts[0]}-{parts[1]}"
            else:
                dt_str = raw_dt.replace(':', '-') # 안전을 위한 Fallback
        else:
            # 2. 메타데이터 누락 시 -> 상위 폴더 이름에서 힌트 얻기 (예: D:\사진집\2014 겨울여행\IMG_01.jpg)
            # 폴더명에 2014 같은 4자리 숫자 연도가 있는지 정규식으로 유추
            parent_dir = os.path.basename(os.path.dirname(filepath))
            grandparent_dir = os.path.basename(os.path.dirname(os.path.dirname(filepath)))
            
            match = re.search(r'(19|20)\d{2}[-._]?\d{0,2}', parent_dir + grandparent_dir)
            if match:
                dt_str = match.group()
        
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
    # 📝 4단계: 파일명 정규화 (Renaming)
    # ==========================
    def generate_clean_filename(self, dt_str, sequence_idx, original_ext):
        """뒤죽박죽 원본 파일명을 '2023-10-15_01.jpg' 꼴로 예쁘게 만듦"""
        # 시간순 정렬 후 전달받은 sequence_idx로 일련번호(_01, _02) 부여
        return f"{dt_str}_{sequence_idx:02d}{original_ext}"

    # ==========================
    # ⚙️ 실행: 파이프라인 메인루프
    # ==========================
    def process_file_metadata(self, filepath):
        """1장의 파일에 대해 중복/Junk 여부를 판단하고 날짜/이름/경로를 계산"""
        is_junk, junk_reason = self.is_junk_or_duplicate(filepath)
        if is_junk:
            return {"status": "JUNK", "reason": junk_reason}

        dt_str, loc_str = self.extract_datetime_and_location(filepath)
        # 예: 2023-10-15
        return {
            "status": "VALID",
            "dt_str": dt_str,
            "loc_str": loc_str,
            "hash": junk_reason # is_junk_or_duplicate 반환값 튜플의 [1]은 False일 때 hash 반환함 
        }

    def run(self):
        print("🚀 [GumaPhoto Pipeline] 데이터 정리를 시작합니다...")
        
        # 1. 대상 파일 스캔
        all_files = []
        for root, _, files in os.walk(SOURCE_DIR):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.heic', '.mp4', '.mov', '.avi', '.mkv']:
                    all_files.append(os.path.join(root, file))
        
        print(f"[*] 총 {len(all_files)}개의 미디어 파일이 발견되었습니다.")
        
        # 2. 메타데이터 파싱 및 시계열 그룹핑 (날짜별 묶음)
        # 구조: { "2023-10-15": [ {filepath, dt_str, md5...}, ... ] }
        date_groups = {}
        junk_count = 0
        
        print("[*] 1차 스캔: 메타데이터 분석 및 찌꺼기/중복 제거 중... (시간이 걸릴 수 있습니다)")
        # --- TEST를 위해 일단 100개만 스캔해볼게 ---
        for i, filepath in enumerate(all_files):
            # 개발 테스트 단계이므로 10262장은 너무 많아. 10개만 샘플 테스트!
            if i >= 10: break

            meta = self.process_file_metadata(filepath)
            
            if meta["status"] == "JUNK":
                print(f"   🗑️ [JUNK 삭제] {os.path.basename(filepath)} -> 사유: {meta['reason']}")
                junk_count += 1
                continue
            
            # 여기서 실제로는 시간(시:분:초)도 파싱해서 배열에 담아야 sorting이 가능함 (현재는 mock)
            dt_key = meta["dt_str"]
            if dt_key not in date_groups:
                date_groups[dt_key] = []
                
            date_groups[dt_key].append({
                "filepath": filepath,
                "loc_str": meta["loc_str"]
            })
            
        print(f"[*] 1차 스캔 완료. 총 {junk_count}개의 찌꺼기 파일이 무시되었습니다.")
        
        # 3. 그룹별 일련번호 부여 및 폴더 이동 시뮬레이션
        print("\n[*] 2차 처리: 날짜별 정렬, 이름 변경 및 최종 이동 시뮬레이션")
        for date, items in date_groups.items():
            # (원래는 여기서 timestamp 기준으로 sort를 해야함)
            
            for index, item in enumerate(items):
                sequence = index + 1
                ext = os.path.splitext(item["filepath"])[1].lower()
                
                # 4단계: 파일명 정규화 (YYYY-MM-DD_01.jpg)
                new_filename = self.generate_clean_filename(date, sequence, ext)
                
                # 연도 폴더 1뎁스 추출 (예: '2023')
                year_folder = str(date).split('-')[0] if '-' in str(date) else 'Unknown_Year'
                
                # 최종 도착 경로 (예: TARGET_DIR/2023/2023-10-15_Unknown_Location/2023-10-15_01.jpg)
                target_folder_path = os.path.join(TARGET_DIR, year_folder, f"{date}_{item['loc_str']}")
                final_move_path = os.path.join(target_folder_path, new_filename)
                
                print(f"   🚚 [복사 진행] {os.path.basename(item['filepath'])} -> {os.path.relpath(final_move_path, TARGET_DIR)}")
                
                os.makedirs(target_folder_path, exist_ok=True)
                
                # 안전장치: 원본 유지(이동/삭제 없음)를 위해 메타데이터 보존 복사(copy2)
                if not os.path.exists(final_move_path):
                    shutil.copy2(item['filepath'], final_move_path)
                
                # 5단계: DB에 기록
                file_hash_val = item.get('hash', 'UNKNOWN_HASH')
                self.cursor.execute(
                    "INSERT OR IGNORE INTO processed_files (filepath, file_hash, status) VALUES (?, ?, ?)",
                    (item['filepath'], file_hash_val, 'PROCESSED')
                )
                
        self.conn.commit()
        print(f"\n✅ 샘플 자동 정리(복사)가 완료되었습니다! C:/Users/guma3/OneDrive/Pictures/OrganizedPhotos 폴더를 확인해보세요!")

if __name__ == "__main__":
    organizer = OrganizerPipeline()
    organizer.run()
