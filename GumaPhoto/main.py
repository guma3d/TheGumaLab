import os
import shutil
import io
import zipfile
import json
import numpy as np
import pickle
import subprocess
from typing import List, Optional
from fastapi import FastAPI, Request, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sqlite3
import threading
from contextlib import asynccontextmanager

from transformers import AutoProcessor, AutoModel
import torch
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, MatchText, MatchValue
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Global Models & Clients
siglip_processor = None
siglip_model = None
qdrant_client = None
gemini_client = None
known_faces = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global siglip_processor, siglip_model, qdrant_client, gemini_client, known_faces
    
    # 초기 SQLite 테이블 세팅 (Feedback Queue 생성)
    try:
        os.makedirs("/app/data", exist_ok=True)
        conn = sqlite3.connect("/app/data/organizer_state.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                point_id TEXT NOT NULL,
                feedback_text TEXT,
                target_person TEXT,
                status TEXT DEFAULT 'QUEUED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("[*] SQLite Feedback Queue DB synchronized.")
    except Exception as e:
        print(f"[*] DB init error: {e}")
        
    # 얼굴 데이터 로드
    try:
        if os.path.exists("/app/data/known_faces.pkl"):
            with open("/app/data/known_faces.pkl", "rb") as f:
                raw_faces = pickle.load(f)
                valid_faces = 0
                for name, vectors in raw_faces.items():
                    if vectors:
                        # 평균 벡터를 구하고 정규화
                        mean_vec = np.mean(vectors, axis=0)
                        mean_vec = mean_vec / np.linalg.norm(mean_vec)
                        known_faces[name] = mean_vec.tolist()
                        valid_faces += 1
            print(f"[*] Loaded {valid_faces} known faces from learning data.")
        else:
            print("[-] No known_faces.pkl found.")
    except Exception as e:
        print(f"[*] Error loading known_faces.pkl: {e}")

    # Initialize standard SigLIP text/image encoder for High-end queries
    try:
        print("[*] 🖼️ Loading High-End SigLIP (google/siglip-base-patch16-224)...")
        siglip_processor = AutoProcessor.from_pretrained('google/siglip-base-patch16-224')
        siglip_model = AutoModel.from_pretrained('google/siglip-base-patch16-224').to("cuda" if torch.cuda.is_available() else "cpu")
        siglip_model.eval()
    except Exception as e:
        print(f"[-] Failed to load SigLIP model: {e}")
    
    print("[*] Connecting to Qdrant (http://qdrant:6333)...")
    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("[*] Gemini API Key found. Initializing LLM Parser...")
        gemini_client = genai.Client(api_key=gemini_key)
    else:
        print("[!] No GEMINI_API_KEY found. LLM Natural Language Parser is disabled.")
        
    yield
    print("[*] Shutting down GumaPhoto logic...")

app = FastAPI(title="GumaPhoto API", lifespan=lifespan)

# Mount static files correctly
app.mount("/static", StaticFiles(directory="static"), name="static")
# Mount organized photos directory to serve images directly
app.mount("/photos", StaticFiles(directory="/app/data/organized"), name="photos")

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "/app/uploads"
ORGANIZED_DIR = "/app/data/organized"

class SearchRequest(BaseModel):
    query: str
    offset: int = 0
    limit: int = 20
    people: List[str] = []
    location: str = ""
    objects: List[str] = []
    scene: str = ""
    is_load_more: bool = False

class DownloadRequest(BaseModel):
    files: List[str]

class FeedbackRequest(BaseModel):
    filepath: str
    point_id: str
    feedback_text: str

class DeleteRequest(BaseModel):
    filepath: str
    point_id: str

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 전역 락(Lock)을 생성하여 여러 사용자가 동시에 사진을 올려도 스캔 파이프라인이 겹치지 않게 방어
upload_lock = threading.Lock()

def trigger_upload_pipeline():
    """백그라운드에서 실행되는 3순환 업로드 AI 처리 파이프라인"""
    if not upload_lock.acquire(blocking=False):
        print("⏳ [Background] 파이프라인이 이미 맹렬하게 가동 중입니다! (새 사진은 현재 파이프라인이 끝날 때, 혹은 다음 주기에 합류합니다.)")
        return
        
    try:
        print("🚀 [Background] 새 사진 업로드 감지! Organizer 파이프라인을 가동합니다...")
        # 1-2. 자동 날짜 및 장소 인식, 폴더 정리
        subprocess.run(["python", "organizer_pipeline.py"], check=True)
        print("🚀 [Background] 폴더 정리 완료. 이어서 Qdrant Vector Scan을 가동합니다...")
        # 3. 모델 기반 Vector/Payload 분석 후 실시간 DB 등록
        subprocess.run(["python", "vector_indexer.py"], check=True)
        print("✅ [Background] 전체 업로드 파이프라인 성공! 검색 엔진이 실시간 업데이트 되었습니다.")
    except Exception as e:
        print(f"❌ [Background] 파이프라인 가동 중 에러 발생: {e}")
    finally:
        upload_lock.release()

@app.post("/upload/")
async def upload_photos(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_files = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
        
    # 방금 올라온 파일들을 백그라운드 봇이 알아서 치우고 스캔하도록 트리거 발동!
    background_tasks.add_task(trigger_upload_pipeline)
    
    return {
        "message": f"Successfully uploaded {len(files)} files. AI is processing them in the background queue.", 
        "filenames": saved_files
    }

@app.post("/api/search")
async def perform_search(req: SearchRequest):
    if not siglip_model or not qdrant_client:
        raise HTTPException(status_code=500, detail="AI Models are not loaded yet.")
        
    search_text = req.query.strip()
    if not search_text and not req.is_load_more:
        return {"results": []}
        
    enhanced_query = req.scene if req.is_load_more else search_text
    people_detected = req.people if req.is_load_more else []
    location_detected = req.location if req.is_load_more else ""
    objects_detected = req.objects if req.is_load_more else []
    
    # [1] LLM Query Rewriting Layer (Gemini)
    if gemini_client and not req.is_load_more:
        try:
            # 현재 Qdrant에서 보유중인 정확한 Location 리스트 추출 (Scroll Limit 상향 조정)
            existing_locations = []
            try:
                scroll_res = qdrant_client.scroll(collection_name="gumaphoto_hybrid_kr", limit=5000, with_payload=["location"])
                locations_set = {point.payload.get("location") for point in scroll_res[0] if point.payload.get("location")}
                locations_set.discard("Unknown Location")
                locations_set.discard(None)
                existing_locations = list(locations_set)
            except Exception as e:
                print(f"Location Fetch Error: {e}")
                
            prompt = (
                f"사용자 검색어: '{search_text}'\n"
                "당신은 스마트 갤러리의 이미지 검색 쿼리 작성 도우미입니다. "
                "사용자가 한글로 자연어 검색을 하더라도, 반드시 우리가 서버에 '보유하고 있는 태그'를 파악하고 번역(대조)하여 JSON을 구성해야 합니다.\n"
                "다음 규칙에 따라 응답을 반드시 유효한 JSON 형식으로만 작성하세요.\n"
                f"1) 사용자 검색어 중 등록된 가족 이름({list(known_faces.keys())})과 매칭되는 사람이 있다면 'people' 문자열 배열에 저장.\n"
                "2) 사용자 검색어 중 장소/위치/국가명(예: 하와이, 제주도, 미국 등)이 포함되어 있다면, 의미를 스스로 번역/유추하여 다음 <보유 장소 목록> 중 가장 일치하는 텍스트 원본 그대로를 'location'에 문자열로 저장하세요.\n"
                f"   <보유 장소 목록> : {existing_locations}\n"
                "   (핵심 규칙: '하와이'를 검색하면 'Hawaii'나 'Honolulu', '엘에이'를 검색하면 'Los Angeles California' 등 위 목록에 있는 정확한 철자로만 치환해야 합니다. 포함관계에 있는 장소도 매칭 대상입니다. 정합되는 게 없으면 빈 문자열을 넣으세요.)\n"
                "3) 명확한 사물, 옷, 색상 등이 있다면 '영어 소문자 영단어'로 번역하여 'objects' 문자열 배열에 저장. (예: dog, blue shirt, glasses)\n"
                "4) 위 3가지를 제외한 배경, 분위기, 옷의 색, 행동 특징 등은 '순수 영어(English)' 캡션으로 상세히 번역하여 'scene' 문자열에 저장. (오직 영어로만 작성, 예: young girl wearing blue shirt opening refrigerator)\n"
                "예시: {\"people\": [\"송이\"], \"location\": \"Honolulu Hawaii\", \"objects\": [\"dog\", \"blue shirt\"], \"scene\": \"a young girl wearing blue shirt opening refrigerator\"}\n"
                "만약 파악된 값이 없다면 빈 배열이나 빈 문자열로 두세요."
            )
            response = gemini_client.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=prompt,
            )
            import re
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                parsed_opt = json.loads(match.group(0))
                people_detected = parsed_opt.get("people", [])
                location_detected = parsed_opt.get("location", "")
                objects_detected = parsed_opt.get("objects", [])
                enhanced_query = parsed_opt.get("scene", search_text)
                print(f"[Gemini 파싱] 사람: {people_detected}, 장소: '{location_detected}', 사물: {objects_detected}, 상황: '{enhanced_query}'")
            else:
                enhanced_query = response.text.strip()
                location_detected = ""
                objects_detected = []
                print(f"[Gemini 일반 파싱 (JSON 실패)] '{enhanced_query}'")
        except Exception as e:
            print(f"Gemini API Error: {e}")
            location_detected = ""
            objects_detected = []

    # [2 & 3] 메타데이터 역방향 필터링 기반 검색 로직
    try:
        query_filter = None
        must_conditions = []
        
        if people_detected:
            must_conditions.append(
                FieldCondition(
                    key="people",
                    match=MatchAny(any=people_detected)
                )
            )
            
        if location_detected:
            must_conditions.append(
                FieldCondition(
                    key="location",
                    match=MatchText(text=location_detected)
                )
            )

        if objects_detected:
            for obj in objects_detected:
                must_conditions.append(
                    FieldCondition(
                        key="objects",
                        match=MatchValue(value=obj)
                    )
                )
            
        if must_conditions:
            query_filter = Filter(must=must_conditions)

        search_res = []
        
        if enhanced_query.strip() and siglip_processor and siglip_model:
            # 사용자가 인물/장소 외에도 "해변에서 뛰어노는"과 같은 씬(상황)을 명시한 경우
            with torch.no_grad():
                inputs = siglip_processor(text=[enhanced_query], padding="max_length", return_tensors="pt").to(siglip_model.device)
                text_features = siglip_model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
                query_vector = text_features[0].cpu().numpy().tolist()
                
            # Hybrid Search Reranking을 위해 더 넉넉하게 추출
            initial_limit = max(100, req.limit + req.offset)
            raw_points = qdrant_client.query_points(
                collection_name="gumaphoto_hybrid_kr",
                query=query_vector,
                using="scene",
                query_filter=query_filter, # 필터 우선 적용
                limit=initial_limit,
                offset=0,
                with_payload=True
            ).points
            
            # --- [Caption BM25-like Reranking 로직] ---
            import re
            query_words = set(re.findall(r'\b\w+\b', enhanced_query.lower()))
            reranked_points = []
            
            for pt in raw_points:
                caption = pt.payload.get("caption", "").lower()
                caption_words = set(re.findall(r'\b\w+\b', caption))
                
                # 얼마나 많은 검색어 단어가 캡션과 겹치는가?
                overlap_count = len(query_words & caption_words)
                text_score = overlap_count / max(1, len(query_words)) # 0.0 ~ 1.0
                
                # SigLIP Vector Score (가중치 70%) + Florence Text Score (가중치 30%)
                final_score = (pt.score * 0.7) + (text_score * 0.3)
                reranked_points.append((final_score, pt))
                
            # 합산 점수(final_score) 내림차순 정렬
            reranked_points.sort(key=lambda x: x[0], reverse=True)
            
            # 클라이언트가 요청한 Limit/Offset 분량만큼 자르고 Points만 추출
            search_res = [pt for _, pt in reranked_points[req.offset : req.offset + req.limit]]
            
        else:
            # 씬(장면) 설명 없이 인물과 장소만으로 검색한 경우 (예: "성욱이 라스베가스")
            if people_detected:
                p = people_detected[0]
                if p in known_faces:
                    face_vector = known_faces[p]
                    search_res = qdrant_client.query_points(
                        collection_name="gumaphoto_hybrid_kr",
                        query=face_vector,
                        using="face",
                        query_filter=query_filter,
                        limit=req.limit,
                        offset=req.offset,
                        with_payload=True
                    ).points
            elif query_filter:
                # 얼굴도 장면도 없이 장소필터만 있는 경우 (벡터 검색 대신 스크롤 조회)
                # Scroll uses point ID for offset, so we use vector search with dummy vector to use integer offset sorting by similarity
                dummy_vector = [0.0] * 768 # ViT-L-14 dimension
                search_res = qdrant_client.query_points(
                    collection_name="gumaphoto_hybrid_kr",
                    query=dummy_vector,
                    using="scene",
                    query_filter=query_filter,
                    limit=req.limit,
                    offset=req.offset,
                    with_payload=True
                ).points 
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # [4] Parsing Results for UI
    results = []
    for hit in search_res:
        payload = getattr(hit, "payload", {}) or {}
        filepath = payload.get("filepath", "")
        # Convert absolute container path to relative URL route
        # e.g., /app/data/organized/2014-05/2014-05_01.jpg -> /photos/2014-05/2014-05_01.jpg
        photo_url = filepath.replace("/app/data/organized", "/photos")
        
        # 스크롤 검색일 경우 score가 없으므로 1.0 부여
        score_val = getattr(hit, "score", 1.0)
        
        photo_date = payload.get("date", "")
        if not photo_date:
            # 파일 경로에서 날짜 추출 Fallback
            import re
            date_match = re.search(r'(19|20)\d{2}-\d{2}(-\d{2})?', os.path.basename(filepath))
            photo_date = date_match.group(0) if date_match else ""

        results.append({
            "id": hit.id,
            "score": round(score_val, 4),
            "url": photo_url,
            "original_path": filepath,
            "date": photo_date,
            "location": payload.get("location", ""),
            "time_of_day": payload.get("time_of_day", ""),
            "season": payload.get("season", ""),
            "people": payload.get("people", [])
        })
        
    return {
        "original_query": search_text,
        "enhanced_query": enhanced_query,
        "results": results,
        "people_detected": people_detected,
        "location_detected": location_detected,
        "objects_detected": objects_detected,
        "total_hits": len(results)
    }

@app.post("/api/download")
async def download_photos(req: DownloadRequest):
    """
    Requested file URLs from UI (/photos/YYYY/...)
    We will map them back to /app/data/organized/... and zip them.
    """
    if not req.files:
        raise HTTPException(status_code=400, detail="No files selected.")
        
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_url in req.files:
            # Map /photos/xxx to /app/data/organized/xxx
            actual_path = file_url.replace("/photos", ORGANIZED_DIR)
            if os.path.exists(actual_path):
                filename = os.path.basename(actual_path)
                zip_file.write(actual_path, arcname=filename)
                
    zip_buffer.seek(0)
    
    response = StreamingResponse(zip_buffer, media_type="application/zip")
    response.headers["Content-Disposition"] = "attachment; filename=GumaPhoto_Export.zip"
    return response

@app.post("/api/feedback")
async def receive_feedback(req: FeedbackRequest):
    """
    모달 창에서 사용자가 남긴 "이건 송이가 아니고 성욱이야" 피드백을 받아
    1장 즉시 학습 및 Qdrant 태그 갱신(Patch) 처리
    """
    if not gemini_client or not qdrant_client:
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
        response = gemini_client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
        )
        
        raw_text = response.text.strip()
        # 마크다운 ```json 제거 방어코드
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
    
    # 1.5 만약 가족 생년월일이나 성별이 새롭게 피드백에 있다면 family_meta.json 즉시 업데이트
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
        abs_path = abs_path.replace("/videos", "/app/data/organized")
    elif abs_path.startswith("/photos/"):
        abs_path = abs_path.replace("/photos", "/app/data/organized")
    
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Original photo file not found on disk.")
        
    img = cv2.imread(abs_path)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not read the image file.")
        
    # 메모리 방어를 위해 여기서만 잠깐 가동하고 내림 
    print("   🤖 [InsightFace] Extracting vectors for local feedback...")
    face_app = FaceAnalysis(name='buffalo_l', root='/root/.insightface')
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    faces = face_app.get(img)
    
    if not faces:
        raise HTTPException(status_code=400, detail="No faces detected in this photo.")
        
    # 얼굴 면적이 가장 큰 피사체(주인공) 하나만 뽑기
    largest_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    new_vector = largest_face.embedding.tolist()
    
    # [3] known_faces.pkl에 배열로 추가 (Appending Knowledge)
    global known_faces
    try:
        pkl_path = "/app/data/known_faces.pkl"
        raw_faces = {}
        if os.path.exists(pkl_path):
            with open(pkl_path, "rb") as f:
                raw_faces = pickle.load(f)
                
        if target_person not in raw_faces:
            raw_faces[target_person] = []
            
        raw_faces[target_person].append(new_vector)
        
        # 즉시 덮어쓰기 저장!
        with open(pkl_path, "wb") as f:
            pickle.dump(raw_faces, f)
            
        # 메인 메모리 변수(평균 벡터)도 실시간 갱신 (서버 재시작 없이 바로 검색 가능하게)
        v_array = raw_faces[target_person]
        mean_vec = np.mean(v_array, axis=0)
        mean_vec = mean_vec / np.linalg.norm(mean_vec)
        known_faces[target_person] = mean_vec.tolist()
        
        print(f"   📚 [AI 학습] '{target_person}'의 얼굴 벡터가 추가로 학습되었습니다. (총 데이터 {len(raw_faces[target_person])}장)")
        
    except Exception as e:
        print(f"   ❌ Pickle Save Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save learning data.")
        
    # [4] Qdrant DB 해당 사진 즉각 Payload 패치 (Local Done)
    try:
        update_payload = {}
        if target_person: update_payload["people"] = [target_person]
        if target_loc: update_payload["location"] = target_loc
        if target_date: update_payload["date"] = target_date

        if update_payload:
            qdrant_client.set_payload(
                collection_name="gumaphoto_hybrid_kr",
                payload=update_payload,
                points=[req.point_id]
            )
            print(f"   ⚡ [Qdrant] 메타데이터가 UI 검색에 즉시 반영되도록 패치되었습니다.")
    except Exception as e:
        print(f"   ❌ Qdrant Patch Error: {e}")
        
    # [5] SQLite Queue 스케줄 추가 (LOCAL_DONE)
    try:
        conn = sqlite3.connect("/app/data/organizer_state.db")
        # 컬럼에 location과 date가 없다면 추가 (마이그레이션 방어)
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

@app.delete("/api/photos")
async def delete_photo(req: DeleteRequest):
    """
    프론트엔드 모달 기능: 사진 완전 파기 (Hard Delete)
    1. 물리적 파일 삭제
    2. Qdrant 벡터 포인트 삭제
    3. SQLite 스캔 처리 마킹 삭제/DELETED 기록
    """
    abs_path = req.filepath
    if abs_path.startswith("/videos/"):
        abs_path = abs_path.replace("/videos", "/app/data/organized")
    elif abs_path.startswith("/photos/"):
        abs_path = abs_path.replace("/photos", "/app/data/organized")
        
    print(f"🗑️ [완전 삭제 요청] 파일: {abs_path} / Point: {req.point_id}")
    
    # [1] 서버 스토리지 디스크 파일 폭파
    try:
        if os.path.exists(abs_path):
            os.remove(abs_path)
            print(f"   ✅ [1/3] 서버 원본 파일 영구 삭제 완료")
        else:
            print(f"   ⚠️ [1/3] 서버에 파일이 존재하지 않아 파일 삭제는 패스함")
    except Exception as e:
        print(f"   ❌ [1/3] 파일 삭제 중 오류 발생: {e}")
        # 파일이 꼬였더라도 유령 데이터를 지우기 위해 2~3단계는 계속 진행합니다.
        
    # [2] Qdrant DB 포인트 제거
    try:
        if qdrant_client:
            qdrant_client.delete(
                collection_name="gumaphoto_hybrid_kr",
                points_selector=[req.point_id]
            )
            print(f"   ✅ [2/3] Qdrant Vector Data 파기 완료")
    except Exception as e:
        print(f"   ❌ [2/3] Qdrant DB 삭제 중 오류 발생: {e}")
        
    # [3] SQLite 상태 초기화 (DELETED 묘비 세우기)
    try:
        conn = sqlite3.connect("/app/data/organizer_state.db")
        # 벡터라이저가 다시 스캔하는 걸 원천 차단하기 위해 DELETED 로 남겨둠
        conn.execute("UPDATE vectorized_files SET status='DELETED' WHERE filepath=?", (abs_path,))
        conn.commit()
        conn.close()
        print(f"   ✅ [3/3] SQLite DB 유령 스캔 방지 처리 완료")
    except Exception as e:
        print(f"   ❌ [3/3] SQLite 갱신 중 오류 발생: {e}")
        
    return {"message": "Successfully completely deleted the photo.", "deleted_id": req.point_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
