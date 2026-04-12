from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/sw.js")
async def serve_sw():
    return FileResponse("frontend/sw.js")

@router.get("/manifest.json")
async def serve_manifest():
    return FileResponse("frontend/manifest.json")

@router.get("/map")
async def serve_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})
