from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import os
import io
import zipfile
from core.state import state

router = APIRouter()

class DownloadRequest(BaseModel):
    files: List[str]

@router.post("/api/download")
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
            actual_path = file_url.replace("/photos", state.organized_dir)
            if os.path.exists(actual_path):
                filename = os.path.basename(actual_path)
                zip_file.write(actual_path, arcname=filename)
                
    zip_buffer.seek(0)
    
    response = StreamingResponse(zip_buffer, media_type="application/zip")
    response.headers["Content-Disposition"] = "attachment; filename=GumaPhoto_Export.zip"
    return response
