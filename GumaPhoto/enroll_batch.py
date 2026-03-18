import os
import cv2
import pickle
import sys
import numpy as np
from insightface.app import FaceAnalysis

ENROLLED_DIR = "/app/data/enrolled"
PKL_PATH = "/app/data/known_faces.pkl"

def enroll_batch_faces():
    if not os.path.exists(ENROLLED_DIR):
        print(f"❌ '{ENROLLED_DIR}' 폴더가 존재하지 않습니다.")
        return

    print("🚀 [가족 대량 등록 프로세스 시작] (GPU VRAM 보호를 위해 100% 순수 CPU 모드로 안전하게 동작합니다)\n")
    
    # === 절대 안전 수칙: 현재 돌고 있는 백그라운드 인덱서를 위해 GPU 강제 차단 ===
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    
    # 1. CPU 전용 InsightFace 로딩
    print("  👉 InsightFace(CPU 모드) 로딩 중...")
    face_app = FaceAnalysis(name='buffalo_l', root='/root/.insightface', providers=['CPUExecutionProvider'])
    face_app.prepare(ctx_id=-1, det_size=(640, 640))
    
    # 2. 기존 학습 데이터 불러오기
    known_faces = {}
    if os.path.exists(PKL_PATH):
        try:
            with open(PKL_PATH, 'rb') as f:
                known_faces = pickle.load(f)
                print(f"  👉 기존 학습 데이터 로드 성공 (현재 등록된 인물 수: {len(known_faces)}명)")
        except Exception as e:
            print(f"  ⚠️ 기존 데이터 로드 실패. 새로 생성합니다: {e}")
            
    # 3. 폴더 순회하며 얼굴 추출
    total_added = 0
    for person_name in os.listdir(ENROLLED_DIR):
        person_dir = os.path.join(ENROLLED_DIR, person_name)
        if not os.path.isdir(person_dir):
            continue
            
        print(f"\n👤 [{person_name}] 폴더 학습 시작 --------------------")
        
        if person_name not in known_faces:
            known_faces[person_name] = []
            
        added_for_person = 0
        
        # 사진 파일들 검색
        for filename in os.listdir(person_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
                img_path = os.path.join(person_dir, filename)
                
                img = cv2.imread(img_path)
                if img is None:
                    print(f"   ❌ 읽기 실패: {filename}")
                    continue
                    
                # 얼굴 찾기
                faces = face_app.get(img)
                
                if not faces:
                    print(f"   ⚠️ 얼굴 감지 실패: {filename} (사진 구조가 복잡하거나 해상도 문제 등)")
                    continue
                    
                # 여러 명이 찍혀 있어도, "가장 면적이 큰 얼굴 하나(=이 폴더의 주인공)"만 등록 타겟으로 삼음
                largest_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
                
                # 추출한 주인공의 벡터값을 배열에 즉시 추가
                known_faces[person_name].append(largest_face.embedding.tolist())
                added_for_person += 1
                total_added += 1
                
                print(f"   ✅ 특징 등록 완료: {filename} (L2 Norm: {np.linalg.norm(largest_face.embedding):.2f})")
                
        print(f"✨ [{person_name}] 님 완료: 총 {added_for_person}장의 고해상도 얼굴 지문이 학습되었습니다!")
        
    # 4. 최종 저장
    if total_added > 0:
        with open(PKL_PATH, 'wb') as f:
            pickle.dump(known_faces, f)
        print(f"\n🎉 [대량 학습 완료] 총 {total_added}개의 얼굴 데이터베이스가 안전하게 병합 저장되었습니다!")
        print(f"   저장 위치: {PKL_PATH}")
    else:
        print("\n⚠️ 새로 학습할 만큼 유효한 사진을 찾지 못했습니다.")

if __name__ == "__main__":
    enroll_batch_faces()
