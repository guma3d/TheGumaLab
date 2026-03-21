import os
import json
import torch
import pickle
import numpy as np
import re
from insightface.app import FaceAnalysis
try:
    from hsemotion.facial_emotions import HSEmotionRecognizer
except ImportError:
    pass

class FaceEngine:
    def __init__(self):
        print("[*] 👤 InsightFace 얼굴 인식 모델 로드 중 (buffalo_l) ...")
        self.face_app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        
        print("[*] ❤️ HSEmotion 표정 인식기 로드 중 (enet_b0_8_best_vgaf) ...")
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
            print(f"  [!] ⚠️ HSEmotion 로드 실패. 감정 인식 기능 비활성화: {e}")
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

    def analyze_face(self, cv_img, filepath):
        faces = self.face_app.get(cv_img)
        face_count = len(faces)
        
        best_face_payload = {}
        found_people = []
        best_face_vector = None
        
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
            best_face_vector = best_face.normed_embedding.tolist()
            
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
            
            box = best_face.bbox.astype(int)
            x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(cv_img.shape[1], box[2]), min(cv_img.shape[0], box[3])
            face_img = cv_img[y1:y2, x1:x2]
            
            try:
                if face_img.size > 0 and self.emotion_recognizer:
                    emotion, scores = self.emotion_recognizer.predict_emotions(face_img, logits=False)
                    best_face_payload['emotion'] = emotion
                else:
                    best_face_payload['emotion'] = 'neutral'
            except Exception:
                best_face_payload['emotion'] = 'neutral'
        else:
            found_people.append("No People")
            
        return face_count, found_people, best_face_vector, best_face_payload, real_age if face_count > 0 else 0
