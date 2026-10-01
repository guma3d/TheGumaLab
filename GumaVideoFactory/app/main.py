import json
import uuid
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Literal

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.config import (
    PORT, HOST, STORAGE_DIR, PROJECTS_DIR, CLIPS_DIR, AUDIO_DIR, OUTPUTS_DIR,
    PLANNER_MODEL, VEO_MODEL, DEFAULT_VOICE, GEMINI_API_KEY, IMAGES_DIR, IMAGE_MODEL
)
from app.core.planner import plan_video_storyboard, VideoStoryBoard
from app.core.veo_client import generate_video_clip
from app.core.tts_engine import synthesize_speech
from app.core.image_client import generate_preview_image
from app.core.ffmpeg_mixer import concatenate_clips_with_audio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GumaVideoFactory")

app = FastAPI(title="GumaVideoFactory", description="AI 숏폼 영상 제작 및 편집 스튜디오")

# Mount storage as static for video/audio preview playback
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

class CreateProjectRequest(BaseModel):
    idea: str = Field(min_length=1, max_length=5000)
    target_duration: int = 30
    scene_count: int = Field(default=6, ge=6, le=8)
    style_prompt: str = Field(default="Cinematic realistic imagery, consistent warm lighting and restrained colors", min_length=1, max_length=2000)
    aspect_ratio: Literal["9:16", "16:9"] = "9:16"
    voice: str = DEFAULT_VOICE
    model: str = VEO_MODEL

class ReviewRequest(BaseModel):
    narrations: List[str] = Field(min_length=6, max_length=8)
    approved: bool = False


def preview_image_path(project_id: str, scene_number: int) -> Path:
    return IMAGES_DIR / f"{project_id}_scene_{scene_number:02d}.png"


def require_preview(project: dict):
    scenes = (project.get("storyboard") or {}).get("scenes", [])
    if not 6 <= len(scenes) <= 8 or not all(
        s.get("image_url") and preview_image_path(project["id"], s["scene_number"]).is_file()
        for s in scenes
    ):
        raise HTTPException(status_code=409, detail="6~8컷의 이미지 프리뷰가 모두 준비되어야 합니다.")

def save_project(project: dict):
    path = PROJECTS_DIR / f"{project['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

def load_project(project_id: str) -> dict:
    path = PROJECTS_DIR / f"{project_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_all_projects() -> List[dict]:
    projects = []
    for file in sorted(PROJECTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(file, "r", encoding="utf-8") as f:
                projects.append(json.load(f))
        except Exception as e:
            logger.warning(f"Failed to read project {file}: {e}")
    return projects

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    projects = list_all_projects()
    has_api_key = bool(GEMINI_API_KEY)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "projects": projects,
            "has_api_key": has_api_key,
            "default_model": VEO_MODEL,
            "planner_model": PLANNER_MODEL,
            "image_model": IMAGE_MODEL,
        }
    )

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "GumaVideoFactory",
        "has_gemini_key": bool(GEMINI_API_KEY),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/projects")
async def get_projects():
    return list_all_projects()

@app.post("/api/projects")
async def create_project(req: CreateProjectRequest, background_tasks: BackgroundTasks):
    project_id = str(uuid.uuid4())[:8]
    project = {
        "id": project_id,
        "idea": req.idea,
        "target_duration": req.scene_count * 4,
        "scene_count": req.scene_count,
        "style_prompt": req.style_prompt,
        "approved_at": None,
        "aspect_ratio": req.aspect_ratio,
        "voice": req.voice,
        "model": req.model,
        "status": "planning",  # planning -> planned -> generating -> ready -> failed
        "progress_message": "AI Director가 스토리보드를 기획 중입니다...",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "storyboard": None,
        "clips": [],
        "audio_url": None,
        "output_video_url": None,
    }
    save_project(project)

    # 비동기로 기획 시작
    background_tasks.add_task(async_plan_and_prepare, project_id)
    return project

async def async_plan_and_prepare(project_id: str):
    try:
        project = load_project(project_id)
        storyboard = await asyncio.to_thread(plan_video_storyboard,
            user_idea=project["idea"],
            target_duration=project["target_duration"],
            aspect_ratio=project["aspect_ratio"],
            scene_count=project["scene_count"],
            style_prompt=project["style_prompt"],
        )
        project["storyboard"] = storyboard.model_dump()
        project["status"] = "previewing"
        save_project(project)
        await prepare_preview_images(project_id)
    except Exception as e:
        logger.error(f"Planning failed for project {project_id}: {e}")
        project = load_project(project_id)
        project["status"] = "failed"
        project["progress_message"] = f"기획 중 오류 발생: {str(e)}"
        save_project(project)


async def prepare_preview_images(project_id: str):
    project = load_project(project_id)
    try:
        scenes = project["storyboard"]["scenes"]
        for scene in scenes:
            path = preview_image_path(project_id, scene["scene_number"])
            if not (scene.get("image_url") and path.is_file()):
                project["progress_message"] = f"컷 {scene['scene_number']}/{len(scenes)} 프리뷰 이미지 생성 중..."
                save_project(project)
                reference = preview_image_path(project_id, 1)
                await asyncio.to_thread(
                    generate_preview_image, scene["visual_prompt"], path,
                    project["aspect_ratio"], project.get("style_prompt", "Cinematic realistic imagery"),
                    reference if scene["scene_number"] != 1 and reference.is_file() else None,
                )
                scene["image_url"] = f"/storage/preview_images/{path.name}"
                save_project(project)
        project["status"] = "preview_ready"
        project["progress_message"] = "이미지와 대본을 확인하고 최종 승인하면 영상 제작이 시작됩니다."
    except Exception:
        logger.exception("Preview generation failed for %s", project_id)
        project["status"] = "preview_failed"
        project["progress_message"] = "이미지 생성에 실패했습니다. 완성된 컷은 유지됩니다. 프리뷰 재시도를 눌러주세요."
    save_project(project)


@app.post("/api/projects/{project_id}/preview")
async def retry_preview(project_id: str, background_tasks: BackgroundTasks):
    project = load_project(project_id)
    if project["status"] not in ["planned", "preview_failed"]:
        raise HTTPException(status_code=409, detail="현재 상태에서는 프리뷰를 재시도할 수 없습니다.")
    if not project.get("storyboard") or not 6 <= len(project["storyboard"]["scenes"]) <= 8:
        raise HTTPException(status_code=409, detail="6~8컷으로 새 프로젝트를 만들어주세요.")
    project["approved_at"] = None
    project["status"] = "previewing"
    save_project(project)
    background_tasks.add_task(prepare_preview_images, project_id)
    return {"message": "Preview started"}

@app.get("/api/projects/{project_id}")
async def get_project_details(project_id: str):
    return load_project(project_id)

@app.post("/api/projects/{project_id}/generate")
async def start_generation(project_id: str, req: ReviewRequest, background_tasks: BackgroundTasks):
    project = load_project(project_id)
    if project["status"] != "preview_ready":
        raise HTTPException(status_code=409, detail="검토 가능한 프리뷰가 준비되어야 합니다.")
    require_preview(project)
    if not req.approved:
        raise HTTPException(status_code=400, detail="최종 승인 후 영상 제작을 시작해주세요.")
    scenes = project["storyboard"]["scenes"]
    if len(req.narrations) != len(scenes) or any(not text.strip() or len(text) > 1000 for text in req.narrations):
        raise HTTPException(status_code=400, detail="각 컷의 대본을 1~1000자로 입력해주세요.")
    for scene, narration in zip(scenes, req.narrations):
        scene["narration_ko"] = narration.strip()
    project["approved_at"] = datetime.now().isoformat()
    
    project["status"] = "generating"
    project["progress_message"] = "Veo 3.1 비디오 및 오디오 클립 생성을 시작합니다..."
    save_project(project)

    background_tasks.add_task(async_generate_video, project_id)
    return {"message": "Generation started", "project_id": project_id}


@app.patch("/api/projects/{project_id}/review")
async def save_review(project_id: str, req: ReviewRequest):
    project = load_project(project_id)
    if project["status"] != "preview_ready":
        raise HTTPException(status_code=409, detail="프리뷰 준비가 완료된 후 대본을 수정할 수 있습니다.")
    scenes = project["storyboard"]["scenes"]
    if len(req.narrations) != len(scenes) or any(not t.strip() or len(t) > 1000 for t in req.narrations):
        raise HTTPException(status_code=400, detail="모든 컷의 대본을 1~1000자로 입력해주세요.")
    for scene, text in zip(scenes, req.narrations):
        scene["narration_ko"] = text.strip()
    project["approved_at"] = None
    save_project(project)
    return {"message": "대본을 저장했습니다."}

async def async_generate_video(project_id: str):
    try:
        project = load_project(project_id)
        storyboard = project["storyboard"]
        scenes = storyboard.get("scenes", [])
        clips = []

        # 1. 씬별 영상 생성
        for idx, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", idx + 1)
            project["progress_message"] = f"씬 {scene_num}/{len(scenes)} 영상 렌더링 중 (Veo 3.1)..."
            save_project(project)

            clip_filename = f"{project_id}_scene_{scene_num:02d}.mp4"
            clip_path = CLIPS_DIR / clip_filename

            await asyncio.to_thread(generate_video_clip,
                prompt=f"{scene['visual_prompt']}\nCamera motion: {scene['camera_movement']}\nPreserve the supplied keyframe's visual style and subject appearance.",
                output_path=clip_path,
                duration_seconds=scene.get("duration_seconds", 5),
                aspect_ratio=project["aspect_ratio"],
                model_name=project.get("model"),
                image_path=preview_image_path(project_id, scene_num),
            )
            clips.append(str(clip_path))
            project["clips"].append(f"/storage/raw_clips/{clip_filename}")
            save_project(project)

        # 2. 나레이션 오디오 합성 (Edge-TTS)
        project["progress_message"] = "대본 나레이션 오디오 합성 중 (Edge-TTS)..."
        save_project(project)

        full_narration = " ".join([s.get("narration_ko", "") for s in scenes if s.get("narration_ko")])
        audio_filename = f"{project_id}_narration.mp3"
        audio_path = AUDIO_DIR / audio_filename

        await synthesize_speech(full_narration, audio_path, voice=project.get("voice", DEFAULT_VOICE))
        project["audio_url"] = f"/storage/audio/{audio_filename}"
        save_project(project)

        # 3. FFmpeg로 1개 숏폼 영상으로 합성
        project["progress_message"] = "클립들을 1개의 숏폼 영상으로 최종 병합 중..."
        save_project(project)

        output_filename = f"{project_id}_final.mp4"
        output_path = OUTPUTS_DIR / output_filename

        await asyncio.to_thread(concatenate_clips_with_audio,
            clip_paths=[Path(c) for c in clips],
            audio_path=audio_path,
            output_path=output_path,
            aspect_ratio=project["aspect_ratio"]
        )

        project["output_video_url"] = f"/storage/outputs/{output_filename}"
        project["status"] = "ready"
        project["progress_message"] = "영상 제작이 성공적으로 완료되었습니다!"
        save_project(project)

    except Exception as e:
        logger.error(f"Generation failed for project {project_id}: {e}")
        project = load_project(project_id)
        project["status"] = "failed"
        project["progress_message"] = f"영상 생성 중 오류 발생: {str(e)}"
        save_project(project)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
