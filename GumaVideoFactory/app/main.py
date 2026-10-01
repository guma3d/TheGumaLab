import json
import uuid
import logging
import asyncio
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image, ImageOps, UnidentifiedImageError
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Literal

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from app.config import (
    PORT, HOST, STORAGE_DIR, PROJECTS_DIR, CLIPS_DIR, AUDIO_DIR, OUTPUTS_DIR,
    PLANNER_MODEL, VEO_MODEL, DEFAULT_VOICE, GEMINI_API_KEY, IMAGES_DIR, IMAGE_MODEL, PRODUCT_IMAGES_DIR
)
from app.core.planner import plan_video_storyboard, VideoStoryBoard
from app.core.veo_client import generate_video_clip
from app.core.tts_engine import synthesize_speech
from app.core.image_client import generate_preview_image
from app.core.ffmpeg_mixer import concatenate_clips_with_audio, render_product_still
from app.core.categories import PRESETS
from app.core.recommendations import load_daily, now_kst
from app.core.source_media import MediaSource, store_media, media_preview, render_source_clip

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
    category: str = "tech"
    recommendation_id: Optional[str] = None
    recommendation_date: Optional[str] = None
    style_prompt: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    aspect_ratio: Literal["9:16", "16:9"] = "9:16"
    voice: str = DEFAULT_VOICE
    model: str = VEO_MODEL

    @field_validator("category")
    @classmethod
    def registered_category(cls, value):
        if value not in PRESETS:
            raise ValueError("등록되지 않은 카테고리입니다.")
        return value

class ReviewRequest(BaseModel):
    narrations: List[str] = Field(min_length=6, max_length=8)
    approved: bool = False
    product_url: str = Field(default="", max_length=2000)


def product_image_path(project_id: str) -> Path:
    return PRODUCT_IMAGES_DIR / f"{project_id}.png"


def validate_product_url(value):
    value = value.strip()
    parsed = urlparse(value)
    if value and (parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password):
        raise HTTPException(status_code=400, detail="상품 링크는 HTTPS 주소로 입력해주세요.")
    return value


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
    if len(project_id) != 8 or any(c not in "0123456789abcdef" for c in project_id):
        raise HTTPException(status_code=404, detail="Project not found")
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
async def index_page(request: Request, category: str = "tech"):
    if category not in PRESETS:
        raise HTTPException(status_code=404, detail="등록되지 않은 카테고리입니다.")
    projects = [p for p in list_all_projects() if p.get("category", "tech") == category]
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
            "recommendations": load_daily(),
            "presets": PRESETS,
            "active_category": category,
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


@app.get("/api/recommendations")
async def get_recommendations(date: Optional[str] = None):
    try:
        return load_daily(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜는 YYYY-MM-DD 형식으로 입력해주세요.")

@app.post("/api/projects")
async def create_project(req: CreateProjectRequest, background_tasks: BackgroundTasks):
    recommendation = None
    if req.recommendation_id:
        try:
            daily = load_daily(req.recommendation_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="추천 날짜가 올바르지 않습니다.")
        recommendation = next((item for item in daily["items"] if item["id"] == req.recommendation_id), None)
        if recommendation is None or recommendation["category"] != req.category:
            raise HTTPException(status_code=404, detail="선택한 카테고리의 추천 아이템을 찾을 수 없습니다.")
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="아이디어를 입력해주세요.")
    if req.recommendation_id:
        # Repeated taps should open the current pending preview, not spend on
        # another plan while the same product is waiting for its photograph.
        for existing in sorted(list_all_projects(), key=lambda p: p.get("created_at", ""), reverse=True):
            if (
                existing.get("category") == req.category
                and (existing.get("recommendation") or {}).get("id") == req.recommendation_id
                and existing.get("recommendation_date", existing.get("created_at", "")[:10]) == (req.recommendation_date or now_kst().strftime("%Y-%m-%d"))
                and existing.get("status") in ("planning", "previewing", "reference_required")
            ):
                return existing
    project_id = str(uuid.uuid4())[:8]
    project = {
        "id": project_id,
        "idea": req.idea,
        "target_duration": req.scene_count * 4,
        "scene_count": req.scene_count,
        "style_prompt": req.style_prompt or PRESETS[req.category]["style"],
        "category": req.category,
        "media_mode": "real" if req.category == "food" else "generated",
        "recommendation": recommendation,
        "recommendation_date": req.recommendation_date or now_kst().strftime("%Y-%m-%d"),
        "product_image_url": None,
        "product_url": "",
        "approved_at": None,
        "aspect_ratio": req.aspect_ratio,
        "voice": req.voice,
        "model": req.model,
        "status": "planning",  # planning -> planned -> generating -> ready -> failed
        "progress_message": "AI Director가 스토리보드를 기획 중입니다...",
        "created_at": now_kst().strftime("%Y-%m-%d %H:%M:%S"),
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
            category=project.get("category", "tech"),
            evidence=json.dumps(project.get("recommendation") or {}, ensure_ascii=False),
        )
        project["storyboard"] = storyboard.model_dump()
        # 결정적인 컷 역할은 모델 응답 대신 서비스에서 확정합니다.
        project["storyboard"]["scenes"][-1]["purpose"] = "product_reveal"
        project["storyboard"]["scenes"][-2]["purpose"] = "summary"
        if project.get("category") == "tech" and not any(s.get("covered_features") for s in project["storyboard"]["scenes"]):
            project["storyboard"]["scenes"][-3]["purpose"] = "supporting_features"
        project["storyboard"]["estimated_total_seconds"] = project["target_duration"]
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
        sources = (project.get("recommendation") or {}).get("media_sources", [])
        real_media = project.get("media_mode") == "real"
        if not real_media and not product_image_path(project_id).is_file():
            project["status"] = "reference_required"
            project["progress_message"] = "제품 외형을 맞추려면 실제 상품 사진을 먼저 등록해주세요. 등록하면 이 사진을 기준으로 프리뷰를 생성합니다."
            save_project(project)
            return
        for scene in scenes:
            if scene.get("purpose") == "product_reveal":
                # 실제 상품 사진은 사용자가 업로드한 뒤 프리뷰에 반영됩니다.
                continue
            path = preview_image_path(project_id, scene["scene_number"])
            if not real_media and (scene["scene_number"] == 1 or scene.get("purpose") == "summary"):
                # Never synthesize the marketed product's exterior, even with a
                # reference: exact product pixels must survive into the video.
                scene["visual_mode"] = "product_photo"
                with Image.open(product_image_path(project_id)) as photo:
                    size = (720, 1280) if project["aspect_ratio"] == "9:16" else (1280, 720)
                    ImageOps.pad(photo.convert("RGB"), size, color="black").save(path, format="PNG")
                scene["image_url"] = f"/storage/preview_images/{path.name}?v={uuid.uuid4().hex[:8]}"
                save_project(project)
                continue
            if real_media:
                # 자동 확보 자료를 컷 순서대로 배치하고 실제 프리뷰에서 검토합니다.
                idx = scene["scene_number"] - 1
                if not scene.get("media_source") and idx < len(sources):
                    candidate = sources[idx]
                    if candidate.get("local_file"):
                        scene["media_source"] = candidate
                if scene.get("media_source"):
                    await asyncio.to_thread(media_preview, MediaSource(**scene["media_source"]), path, project["aspect_ratio"])
                    scene["image_url"] = f"/storage/preview_images/{path.name}"
                    scene["media_url"] = f"/storage/source_media/{scene['media_source']['local_file']}"
                continue
            if not (scene.get("image_url") and path.is_file()):
                scene["visual_mode"] = "mechanism_concept"
                project["progress_message"] = f"컷 {scene['scene_number']}/{len(scenes)} 프리뷰 이미지 생성 중..."
                save_project(project)
                await asyncio.to_thread(
                    generate_preview_image, (
                        scene["visual_prompt"] + "\nMANDATORY: Only a standalone conceptual mechanism diagram. "
                        "Do not show any complete product, phone, device enclosure, product exterior, "
                        "camera housing or invented exact product layout. Use isolated optical elements, "
                        "aperture blades, rays, chip blocks or schematic components appropriate to the narration. "
                        "The actual product exterior is displayed separately using its real photograph."
                    ), path,
                    project["aspect_ratio"], project.get("style_prompt", "Cinematic realistic imagery"),
                    product_image_path(project_id),
                    (project.get("recommendation") or {}).get("product_keyword", project["idea"]),
                )
                scene["image_url"] = f"/storage/preview_images/{path.name}"
                save_project(project)
        project["status"] = "preview_ready"
        project["progress_message"] = "실사 자료·대본을 검토해주세요. 비어 있는 컷에는 사용 가능한 사진·영상을 등록하고 상품 사진·링크 확인 후 승인해주세요." if real_media else "이미지·대본을 확인하고 실제 상품 사진과 링크를 등록한 뒤 최종 승인해주세요."
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


@app.post("/api/projects/{project_id}/product-image")
async def upload_product_image(project_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    project = load_project(project_id)
    if project["status"] not in ("reference_required", "planned", "preview_failed", "preview_ready") or not project.get("storyboard"):
        raise HTTPException(status_code=409, detail="대본 준비 후 상품 사진을 등록해주세요.")
    previous_photo = product_image_path(project_id).read_bytes() if product_image_path(project_id).is_file() else None
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="상품 사진은 10MB 이하로 등록해주세요.")
    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in ("JPEG", "PNG", "WEBP") or image.width * image.height > 25000000:
                raise ValueError("Unsupported image")
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.save(product_image_path(project_id), format="PNG")
            # 모든 컷을 같은 720p 캔버스로 맞춰 최종 합성을 안정화합니다.
            size = (720, 1280) if project["aspect_ratio"] == "9:16" else (1280, 720)
            ImageOps.pad(image, size, color="black").save(preview_image_path(project_id, len(project["storyboard"]["scenes"])), format="PNG")
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="정상적인 PNG/JPEG/WebP 상품 사진을 등록해주세요.")
    project["product_image_url"] = f"/storage/product_images/{project_id}.png?v={uuid.uuid4().hex[:8]}"
    project["storyboard"]["scenes"][-1]["image_url"] = project["product_image_url"]
    project["approved_at"] = None
    if project.get("media_mode") != "real" and (
        previous_photo != product_image_path(project_id).read_bytes()
        or project["status"] == "reference_required"
        or any(scene.get("visual_mode") not in ("product_photo", "mechanism_concept") for scene in project["storyboard"]["scenes"][:-1])
    ):
        for scene in project["storyboard"]["scenes"][:-1]:
            scene["image_url"] = None
        project["status"] = "previewing"
        project["progress_message"] = "등록한 상품 사진을 기준으로 프리뷰를 생성합니다..."
        background_tasks.add_task(prepare_preview_images, project_id)
    save_project(project)
    return {"message": "상품 사진을 등록했습니다."}

@app.post("/api/projects/{project_id}/scenes/{scene_number}/media")
async def upload_scene_media(project_id: str, scene_number: int, file: UploadFile = File(...), metadata: str = Form(...)):
    project = load_project(project_id)
    scenes = (project.get("storyboard") or {}).get("scenes", [])
    if project.get("media_mode") != "real" or project["status"] != "preview_ready" or not 1 <= scene_number < len(scenes):
        raise HTTPException(status_code=409, detail="실사 프리뷰의 상품 컷 이전 장면에만 자료를 등록할 수 있습니다.")
    try:
        source = MediaSource.model_validate_json(metadata)
        content = await file.read(40 * 1024 * 1024 + 1)
        source.local_file = await asyncio.to_thread(store_media, content, source.kind)
        path = preview_image_path(project_id, scene_number)
        # 실패 시 기존 프리뷰를 유지합니다.
        staged = path.with_name(path.stem + "_staged.png")
        await asyncio.to_thread(media_preview, source, staged, project["aspect_ratio"])
        staged.replace(path)
    except Exception:
        raise HTTPException(status_code=400, detail="정상 사진/MP4 파일과 출처·제작자·사용 조건·표기 내용을 확인해주세요.")
    scene = scenes[scene_number - 1]
    scene["media_source"] = source.model_dump()
    scene["image_url"] = f"/storage/preview_images/{path.name}?v={uuid.uuid4().hex[:8]}"
    scene["media_url"] = f"/storage/source_media/{source.local_file}"
    project["approved_at"] = None
    save_project(project)
    return {"message": "실사 자료를 등록했습니다."}


@app.post("/api/projects/{project_id}/generate")
async def start_generation(project_id: str, req: ReviewRequest, background_tasks: BackgroundTasks):
    project = load_project(project_id)
    if project["status"] != "preview_ready":
        raise HTTPException(status_code=409, detail="검토 가능한 프리뷰가 준비되어야 합니다.")
    require_preview(project)
    if project.get("media_mode") == "real":
        try:
            for scene in project["storyboard"]["scenes"][:-1]:
                MediaSource(**scene["media_source"]).file_path()
        except (ValueError, KeyError):
            raise HTTPException(status_code=409, detail="모든 실사 컷의 자료와 사용 조건이 준비되어야 합니다.")
    if not req.approved:
        raise HTTPException(status_code=400, detail="최종 승인 후 영상 제작을 시작해주세요.")
    if project.get("category"):
        if not product_image_path(project_id).is_file():
            raise HTTPException(status_code=409, detail="최종 컷에 사용할 실제 상품 사진을 등록해주세요.")
        if project.get("media_mode") != "real" and any(scene.get("visual_mode") not in ("product_photo", "mechanism_concept") for scene in project["storyboard"]["scenes"][:-1]):
            raise HTTPException(status_code=409, detail="제품 외형 보호 기준으로 프리뷰를 다시 준비해야 합니다. 상품 사진을 다시 등록해주세요.")
        if not req.product_url.strip():
            raise HTTPException(status_code=400, detail="상품 링크를 입력해주세요.")
        project["product_url"] = validate_product_url(req.product_url)
    scenes = project["storyboard"]["scenes"]
    if len(req.narrations) != len(scenes) or any(not text.strip() or len(text) > 1000 for text in req.narrations):
        raise HTTPException(status_code=400, detail="각 컷의 대본을 1~1000자로 입력해주세요.")
    for scene, narration in zip(scenes, req.narrations):
        scene["narration_ko"] = narration.strip()
    project["approved_at"] = now_kst().isoformat()
    
    project["status"] = "generating"
    project["progress_message"] = "실제 사진·영상 편집과 나레이션 합성을 시작합니다..." if project.get("media_mode") == "real" else "Veo 3.1 비디오 및 오디오 클립 생성을 시작합니다..."
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
    project["product_url"] = validate_product_url(req.product_url)
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
            project["progress_message"] = f"씬 {scene_num}/{len(scenes)} " + ("실제 사진·영상 편집 중..." if project.get("media_mode") == "real" else "영상 렌더링 중 (Veo 3.1)...")
            save_project(project)

            clip_filename = f"{project_id}_scene_{scene_num:02d}.mp4"
            clip_path = CLIPS_DIR / clip_filename

            if scene.get("purpose") == "product_reveal" or scene.get("visual_mode") == "product_photo":
                await asyncio.to_thread(render_product_still, product_image_path(project_id), clip_path, project["aspect_ratio"])
            elif project.get("media_mode") == "real":
                await asyncio.to_thread(render_source_clip, MediaSource(**scene["media_source"]), clip_path, project["aspect_ratio"], scene.get("duration_seconds", 4))
            else:
                last_image = preview_image_path(project_id, len(scenes)) if scene.get("purpose") == "transition" and product_image_path(project_id).exists() else None
                await asyncio.to_thread(generate_video_clip,
                    prompt=f"{scene['visual_prompt']}\nCamera motion: {scene['camera_movement']}\nPreserve the supplied keyframe's visual style and subject appearance. Animate only the isolated conceptual mechanism. Never add a complete product, product exterior, device enclosure or phone housing." + (
                        "\nSmoothly transform the animated food scene into the supplied real product end frame. Match framing and finish on that exact photo; preserve packaging and text." if last_image else ""
                    ),
                    output_path=clip_path,
                    duration_seconds=scene.get("duration_seconds", 4),
                    aspect_ratio=project["aspect_ratio"],
                    model_name=project.get("model"),
                    image_path=preview_image_path(project_id, scene_num),
                    last_image_path=last_image,
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
        credits = []
        for scene in scenes:
            source = scene.get("media_source")
            if source:
                credit = f"{source['title']} — {source['creator']}\n{source['source_url']}\n{source['license']} ({source['license_url']})\n{source['attribution']}\n편집: 발췌·화면 비율 조정·나레이션 추가"
                if credit not in credits:
                    credits.append(credit)
        if credits:
            credit_path = OUTPUTS_DIR / f"{project_id}_credits.txt"
            credit_path.write_text("\n\n".join(credits), encoding="utf-8")
            project["credits_url"] = f"/storage/outputs/{credit_path.name}"
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
