from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
import sqlite3
import numpy as np
import pickle
from core.state import state

router = APIRouter()

class FeedbackRequest(BaseModel):
    filepath: str
    point_id: str
    feedback_text: str

@router.post("/api/feedback")
async def receive_feedback(req: FeedbackRequest):
    """
    모달 창에서 사용자가 남긴 "이건 송이가 아니고 성욱이야" 피드백을 받아
    1장 즉시 학습 및 Qdrant 태그 갱신(Patch) 처리
    """
    if not state.gemini_client or not state.qdrant_client:
        raise HTTPException(status_code=500, detail="AI/DB Models not fully loaded.")
        
    print(f"📥 [피드백 수신] 사진: {req.filepath} / 내용: {req.feedback_text}")
    
    # [1] LLM에 파싱 맡겨서 메타데이터(장소, 시간, 사람, 성별, 나이)를 종합적으로 추출
    try:
        prompt = (
            f"사용자 피드백 코멘트: '{req.feedback_text}'\n"
            "이 문장을 읽고 사용자가 정정하거나 등록하고자 하는 핵심 정보들을 파싱해줘.\n"
            "결과는 반드시 아래의 JSON 형식으로만 반환해야 해 (다른 말이나 마크다운은 절대 쓰지 마):\n"
            "{\n"
            '  "target_person": "사람 이름 (보통 2~3글자 한국 이름, 없으면 null)",\n'
            '  "target_gender": "여성 또는 남성 (없으면 null)",\n'
            '  "target_birth_year": "태어난 연도 숫자 (예: 2018, 없으면 null)",\n'
            '  "target_location": "장소 또는 위치 이름 (예: 제주도, 롯데월드, 없으면 null)",\n'
            '  "target_date_month": "YYYY-MM 형태의 시간 (예: 2021-08, 1999-12, 없으면 null)"\n'
            "}"
        )
        response = state.gemini_client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        parsed_data = json.loads(raw_text.strip())
        target_person = parsed_data.get("target_person")
        target_gender = parsed_data.get("target_gender")
        target_birth = parsed_data.get("target_birth_year")
        target_loc = parsed_data.get("target_location")
        target_date = parsed_data.get("target_date_month")
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise HTTPException(status_code=400, detail="LLM could not parse the feedback.")
        
    print(f"   🎯 [LLM 자연어 파싱 완료] : {parsed_data}")
    
    if target_person and (target_gender or target_birth):
        try:
            meta_path = "/app/data/family_meta.json"
            family_meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    family_meta = json.load(f)
                    
            if target_person not in family_meta:
                family_meta[target_person] = {}
                
            if target_gender: family_meta[target_person]["gender"] = target_gender
            if target_birth: family_meta[target_person]["birth_year"] = int(target_birth)
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(family_meta, f, ensure_ascii=False, indent=4)
            print(f"   👨‍👩‍👦 [Family Meta Data] '{target_person}'의 신원 정보가 업데이트 되었습니다.")
        except Exception as e:
            print(f"Family Meta Update Error: {e}")
    
    # [2] 사진에서 가장 큰 얼굴의 벡터(512d) 뽑아내기
    import cv2
    from insightface.app import FaceAnalysis
    
    abs_path = req.filepath
    if abs_path.startswith("/videos/"):
        abs_path = abs_path.replace("/videos/", "/app/data/organized/")
    elif abs_path.startswith("/photos/"):
        abs_path = abs_path.replace("/photos/", "/app/data/organized/")
    
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Original photo file not found on disk.")
        
    img = cv2.imread(abs_path)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not read the image file.")
        
    print("   🤖 [InsightFace] Extracting vectors for local feedback...")
    face_app = FaceAnalysis(name='buffalo_l', root='/root/.insightface')
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    faces = face_app.get(img)
    
    if not faces:
        raise HTTPException(status_code=400, detail="No faces detected in this photo.")
        
    largest_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    new_vector = largest_face.embedding.tolist()
    
    try:
        pkl_path = "/app/data/known_faces.pkl"
        raw_faces = {}
        if os.path.exists(pkl_path):
            with open(pkl_path, "rb") as f:
                raw_faces = pickle.load(f)
                
        if target_person not in raw_faces:
            raw_faces[target_person] = []
            
        raw_faces[target_person].append(new_vector)
        
        with open(pkl_path, "wb") as f:
            pickle.dump(raw_faces, f)
            
        v_array = raw_faces[target_person]
        mean_vec = np.mean(v_array, axis=0)
        mean_vec = mean_vec / np.linalg.norm(mean_vec)
        state.known_faces[target_person] = mean_vec.tolist()
        
        print(f"   📚 [AI 학습] '{target_person}'의 얼굴 벡터가 추가로 학습되었습니다. (총 데이터 {len(raw_faces[target_person])}장)")
        
    except Exception as e:
        print(f"   ❌ Pickle Save Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save learning data.")
        
    try:
        update_payload = {}
        if target_person: update_payload["people"] = [target_person]
        if target_loc: update_payload["location"] = target_loc
        if target_date: update_payload["date"] = target_date

        if update_payload:
            state.qdrant_client.set_payload(
                collection_name="gumaphoto_hybrid_kr",
                payload=update_payload,
                points=[req.point_id]
            )
            print(f"   ⚡ [Qdrant] 메타데이터가 UI 검색에 즉시 반영되도록 패치되었습니다.")
            
            try:
                from api.utils.metadata import generate_xmp_sidecar
                point_info = state.qdrant_client.retrieve(collection_name="gumaphoto_hybrid_kr", ids=[req.point_id])
                if point_info:
                    final_payload = point_info[0].payload
                    if final_payload:
                        generate_xmp_sidecar(abs_path, final_payload)
            except Exception as xe:
                print(f"   ❌ XMP Sidecar Patch Error: {xe}")
                
    except Exception as e:
        print(f"   ❌ Qdrant Patch Error: {e}")
        
    try:
        conn = sqlite3.connect(state.db_path)
        try: conn.execute("ALTER TABLE feedback_queue ADD COLUMN parsed_location TEXT")
        except: pass
        try: conn.execute("ALTER TABLE feedback_queue ADD COLUMN parsed_date TEXT")
        except: pass
        
        conn.execute(
            "INSERT INTO feedback_queue (filepath, point_id, feedback_text, target_person, parsed_location, parsed_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (abs_path, req.point_id, req.feedback_text, target_person, target_loc, target_date, 'LOCAL_DONE')
        )
        conn.commit()
        conn.close()
        print(f"   ✅ [DB Queue] 주간 '시공간 전파 재학습' 스케줄에 대기 등록 완료.")
    except Exception as e:
        print(f"   ❌ SQLite Insert Error: {e}")
        
    return {"message": "Success"}
