import os
import shutil
import io
import zipfile
from typing import List, Optional
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Global Models & Clients
clip_model = None
qdrant_client = None
gemini_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global clip_model, qdrant_client, gemini_client
    print("[*] Loading Multilingual CLIP model for Semantic Search...")
    clip_model = SentenceTransformer('clip-ViT-B-32-multilingual-v1')
    
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

class DownloadRequest(BaseModel):
    files: List[str]

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_photos(files: List[UploadFile] = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_files = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
    return {"message": f"Successfully uploaded {len(files)} files.", "filenames": saved_files}

@app.post("/api/search")
async def perform_search(req: SearchRequest):
    if not clip_model or not qdrant_client:
        raise HTTPException(status_code=500, detail="AI Models are not loaded yet.")
        
    search_text = req.query.strip()
    if not search_text:
        return {"results": []}
        
    enhanced_query = search_text
    
    # [1] LLM Query Rewriting Layer (Gemini)
    if gemini_client:
        try:
            prompt = (
                f"사용자 검색어: '{search_text}'\n"
                "당신은 스마트 갤러리의 이미지 검색 쿼리 작성 도우미입니다. "
                "사용자의 요청을 분석해서 CLIP 이미지 임베딩 모델(다국어)이 아주 쉽게 찾을 수 있도록 "
                "간결하고 직관적인 '한국어+영어' 혼합 명사형 캡션(1문장 이내)으로 바꿔주세요. "
                "부연 설명이나 마크다운 없이 오직 변환된 검색어만 출력하세요. "
                "(예: 해변가에서 노는 가족 사진 -> 가족, 해변가, 바다, 웃음, family at the beach playing)"
            )
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            enhanced_query = response.text.strip()
            print(f"[Gemini 파싱] '{search_text}' -> '{enhanced_query}'")
        except Exception as e:
            print(f"Gemini API Error: {e}")

    # [2] Vectorize the Text Query (CLIP Text Encoder)
    query_vector = clip_model.encode(enhanced_query).tolist()
    
    # [3] Search Qdrant DB ('scene' Named Vector)
    try:
        search_res = qdrant_client.search(
            collection_name="gumaphoto_hybrid_kr",
            query_vector=("scene", query_vector),
            limit=50,
            with_payload=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # [4] Parsing Results for UI
    results = []
    for hit in search_res:
        payload = hit.payload or {}
        filepath = payload.get("filepath", "")
        # Convert absolute container path to relative URL route
        # e.g., /app/data/organized/2014-05/2014-05_01.jpg -> /photos/2014-05/2014-05_01.jpg
        photo_url = filepath.replace("/app/data/organized", "/photos")
        
        results.append({
            "id": hit.id,
            "score": round(hit.score, 4),
            "url": photo_url,
            "original_path": filepath,
            "context": payload.get("original_context", ""),
            "date": payload.get("exif_date", ""),
            "emotion": payload.get("emotion", ""),
            "age": payload.get("age", 0)
        })
        
    return {
        "original_query": search_text,
        "enhanced_query": enhanced_query,
        "results": results,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
