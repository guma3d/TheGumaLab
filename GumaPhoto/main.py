import os
import shutil
from typing import List
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="GumaPhoto API")

# Mount static files correctly
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")

# 업로드 경로 설정
UPLOAD_DIR = "/app/uploads"

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_photos(files: List[UploadFile] = File(...)):
    # 폴더가 없으면 생성 (docker 연동 시 이미 있지만 안전을 위해)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    saved_files = []
    
    for file in files:
        # 파일 저장 경로 설정
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # 파일 쓰기
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        saved_files.append(file.filename)
        
    return {"message": f"Successfully uploaded {len(files)} files.", "filenames": saved_files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
