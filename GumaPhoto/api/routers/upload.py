from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Request
from typing import List
import os
import shutil
import uuid
import datetime
from core.state import state
from services.background_tasks import trigger_upload_pipeline

router = APIRouter()

@router.post("/upload/")
async def upload_photos(background_tasks: BackgroundTasks, request: Request, files: List[UploadFile] = File(...)):
    print(f"📡 [Upload Tracker] 새 업로드 스트림 수신 시작! IP: {request.client.host}")
    try:
        os.makedirs(state.upload_dir, exist_ok=True)
        saved_files = []
        for file in files:
            print(f"📡 [Upload Tracker] ➡️ 스트림 파싱 중: {file.filename} / 타입: {file.content_type}")
            base, ext = os.path.splitext(file.filename)
            unique_filename = f"{base}_{uuid.uuid4().hex[:6]}{ext}"
            file_path = os.path.join(state.upload_dir, unique_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(unique_filename)
            
        print(f"📡 [Upload Tracker] ✅ 총 {len(saved_files)}장 하드디스크(uploads_raw) 저장 성공! 백그라운드 봇을 트리거합니다.")
        from core.events import publish_event
        publish_event("FileUploaded", payload={"total_files_uploaded": len(saved_files)})
        
        return {
            "message": f"Successfully uploaded {len(files)} files.",
            "filenames": saved_files
        }
    except Exception as e:
        print(f"🚨 [Upload Tracker FATAL ERROR] 파일 수신 중 스트림 절단 및 에러 발생: {str(e)}")
        try:
            with open("/app/data/upload_crash_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now()}] Upload crash: {str(e)}\n")
        except: pass
        return {"message": "Server streaming error", "error": str(e)}
