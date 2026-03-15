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

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, MatchText
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Global Models & Clients
clip_model = None
qdrant_client = None
gemini_client = None
known_faces = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global clip_model, qdrant_client, gemini_client, known_faces
    
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

    # Initialize standard CLIP text/image encoder for High-end queries
    try:
        print("[*] 🖼️ Loading High-End CLIP (clip-ViT-L-14)...")
        clip_model = SentenceTransformer('clip-ViT-L-14')
    except Exception as e:
        print(f"[-] Failed to load CLIP model: {e}")
    
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
    if not clip_model or not qdrant_client:
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
            prompt = (
                f"사용자 검색어: '{search_text}'\n"
                "당신은 스마트 갤러리의 이미지 검색 쿼리 작성 도우미입니다. "
                f"현재 등록된 가족 이름 목록: {list(known_faces.keys())}\n"
                "다음 규칙에 따라 응답을 반드시 유효한 JSON 형식으로만 작성하세요.\n"
                "1) 사용자가 검색한 내용 중 '등록된 가족 이름'과 매칭되는 사람이 있다면 'people' 문자열 배열에 저장.\n"
                "2) 사용자가 검색한 내용 중 '장소나 위치, 국가, 도시명' 등이 있다면 'location' 문자열에 저장.\n"
                "3) 사용자가 검색한 내용 중 명확한 사물, 동물, 물건(강아지, 자동차, 안경 등)이 있다면 COCO 데이터셋 기준의 '영어 소문자 영단어'로 번역하여 'objects' 문자열 배열에 저장. (예: dog, car, tie)\n"
                "4) 인물, 장소, 사물을 제외한 나머지 배경이나 상황, 분위기, 행동 특징 등은 최상위 품질의 '순수 영어(English)' 캡션으로 번역하여 'scene' 문자열에 저장. (오직 영어로만 작성, 예: family playing at the beach with laughter)\n"
                "예시: {\"people\": [\"성욱\"], \"location\": \"라스베가스\", \"objects\": [\"dog\", \"car\"], \"scene\": \"family playing at the beach with laughter\"}\n"
                "만약 파악된 인물, 장소, 사물이 없다면 빈 배열이나 빈 문자열로 두세요."
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
        
        if enhanced_query.strip():
            # 사용자가 인물/장소 외에도 "해변에서 뛰어노는"과 같은 씬(상황)을 명시한 경우
            query_vector = clip_model.encode(enhanced_query).tolist()
            search_res = qdrant_client.query_points(
                collection_name="gumaphoto_hybrid_kr",
                query=query_vector,
                using="scene",
                query_filter=query_filter, # 필터 우선 적용
                limit=req.limit,
                offset=req.offset,
                with_payload=True
            ).points
            
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
    
    # [1] LLM에 파싱 맡겨서 누구로 바꿔달라는 건지 추출
    target_person = "Unknown"
    try:
        prompt = (
            f"사진 피드백 내용: '{req.feedback_text}'\n"
            "이 문장에서 사용자가 이 사진의 대상을 '누구'라고 정정하거나 등록하고 싶어 하는지 등장인물의 이름(보통 2~3글자의 한국 이름)만 딱 한 단어로 말해.\n"
            "예: '성욱'\n"
            "만약 파악할 수 없다면 'Unknown'을 반환해."
        )
        response = gemini_client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
        )
        target_person = response.text.strip().replace("'", "").replace('"', '')
    except Exception as e:
        print(f"Gemini API Error: {e}")
        
    if target_person == "Unknown" or not target_person:
        raise HTTPException(status_code=400, detail="Could not parse target person name from feedback.")
        
    print(f"   🎯 [LLM 타겟 인물 판단] : {target_person}")
    
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
        qdrant_client.set_payload(
            collection_name="gumaphoto_hybrid_kr",
            payload={"people": [target_person]},
            points=[req.point_id]
        )
        print(f"   ⚡ [Qdrant] 사진 1장에 대한 메타데이터가 즉시 수정되었습니다. (Point: {req.point_id})")
    except Exception as e:
        print(f"   ❌ Qdrant Patch Error: {e}")
        
    # [5] SQLite Queue 스케줄 추가 (LOCAL_DONE)
    try:
        conn = sqlite3.connect("/app/data/organizer_state.db")
        conn.execute(
            "INSERT INTO feedback_queue (filepath, point_id, feedback_text, target_person, status) VALUES (?, ?, ?, ?, ?)",
            (abs_path, req.point_id, req.feedback_text, target_person, 'LOCAL_DONE')
        )
        conn.commit()
        conn.close()
        print(f"   ✅ [DB Queue] 주간 스케줄에 반영 대기 등록 완료.")
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
