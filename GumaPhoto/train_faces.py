import os
import cv2
import pickle
import numpy as np
from insightface.app import FaceAnalysis

print("🔥 [수동 학습 개시] 딥러닝 인물 도감 전체 재학습 시작 (InsightFace VRAM 가동)...")
face_app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

new_known_faces = {}
base_enrolled_dir = "/app/data/enrolled"

if os.path.exists(base_enrolled_dir):
    for person_name in os.listdir(base_enrolled_dir):
        person_folder = os.path.join(base_enrolled_dir, person_name)
        if not os.path.isdir(person_folder): continue
        
        person_vectors = []
        for img_name in os.listdir(person_folder):
            img_path = os.path.join(person_folder, img_name)
            img = cv2.imread(img_path)
            if img is None: continue
            faces = face_app.get(img)
            if not faces: continue
            
            # 가장 큰 타겟(주인공 얼굴) 추출
            best_face = sorted(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)[0]
            person_vectors.append(best_face.normed_embedding.tolist())
            
        if person_vectors:
            # 해당 인물의 평균 벡터 연산
            vec_array = np.array(person_vectors)
            mean_vec = np.mean(vec_array, axis=0) if vec_array.ndim > 1 else vec_array
            mean_vec = mean_vec / np.linalg.norm(mean_vec)
            new_known_faces[person_name] = person_vectors
            
            print(f"  [+] '{person_name}' 학습 완료: 총 {len(person_vectors)}장의 사진 데이터 융합 성공.")
            
    # 최종 추출된 도감을 디스크에 밀봉 보존
    import pickle
    with open("/app/data/known_faces.pkl", "wb") as f:
        pickle.dump(new_known_faces, f)

    print("\n✅ 모든 학습이 완료되었습니다! /app/data/known_faces.pkl 에 얼굴 좌표가 저장되었습니다.")
else:
    print(f"❌ {base_enrolled_dir} 경로가 없습니다.")
