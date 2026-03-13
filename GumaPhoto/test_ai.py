import cv2
import numpy as np
import pprint
import urllib.request
import os

# insightface 라이브러리 (onnx 기반 최고 성능)
from insightface.app import FaceAnalysis

img_path = "/app/data/sample.png"

def analyze_faces():
    print(f"[*] 이미지 분석 시작: {img_path}")
    
    # 1. InsightFace 'buffalo_l' 모델 준비 (용량이 작으면서 매우 높은 정확도)
    try:
        app = FaceAnalysis(name='buffalo_l', root='/root/.insightface')
        # ctx_id=0은 GPU 사용 의미, -1은 CPU 사용
        # det_size=(640,640)이 기본 검출 해상도
        app.prepare(ctx_id=0, det_size=(640, 640))
        print("[*] InsightFace 모델 준비 완료")
    except Exception as e:
        print(f"[!] 모델 로드 에러 (우선 CPU 모드로 동작을 시도합니다): {e}")
        app = FaceAnalysis(name='buffalo_l', root='/root/.insightface')
        app.prepare(ctx_id=-1, det_size=(640, 640))

    # 2. 이미지 읽기
    img = cv2.imread(img_path)
    if img is None:
        print(f"[!] 이미지를 읽을 수 없습니다. 경로 확인: {img_path}")
        return

    # 3. 모델 돌리기
    faces = app.get(img)

    print(f"\n=== 🌟 얼굴 분석 결과 (InsightFace) ===")
    print(f"총 {len(faces)}명의 얼굴이 발견되었습니다.\n")

    for i, face in enumerate(faces):
        print(f"--- 얼굴 {i+1} ---")
        
        # 나이/성별 (buffalo_l 모델은 성별, 나이를 매우 정밀하게 예측합니다)
        # face.gender: 1=Male, 0=Female
        gender = '남자(Male)' if face.gender == 1 else '여자(Female)'
        age = int(face.age)
        
        # 얼굴 좌표 박스: [x1, y1, x2, y2]
        bbox = face.bbox.astype(int)
        
        print(f"예측 성별: {gender}")
        print(f"예측 나이: {age}세 (체감 예측일 뿐 실 나이와 다를 수 있음)")
        print(f"얼굴 좌표: x1={bbox[0]}, y1={bbox[1]}, x2={bbox[2]}, y2={bbox[3]}")
        # 임베딩 얼굴 특징점(512차원 배열) 추출 확인 (벡터 DB에 들어갈 놈)
        print(f"얼굴 임베딩 벡터 크기: {face.embedding.shape}")
        print("")


if __name__ == "__main__":
    analyze_faces()
