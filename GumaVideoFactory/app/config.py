import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project folder, then parent folder
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PORT = int(os.getenv("PORT", "8085"))
HOST = os.getenv("HOST", "0.0.0.0")

PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gemini-3.8-flash")
VEO_MODEL = os.getenv("VEO_MODEL", "veo-3.1-fast-generate-preview")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-2.5-flash-image")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "ko-KR-SunHiNeural")

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
PROJECTS_DIR = STORAGE_DIR / "projects"
CLIPS_DIR = STORAGE_DIR / "raw_clips"
AUDIO_DIR = STORAGE_DIR / "audio"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
IMAGES_DIR = STORAGE_DIR / "preview_images"
PRODUCT_IMAGES_DIR = STORAGE_DIR / "product_images"
RECOMMENDATIONS_DIR = STORAGE_DIR / "recommendations"
SOURCE_MEDIA_DIR = STORAGE_DIR / "source_media"

for d in [STORAGE_DIR, PROJECTS_DIR, CLIPS_DIR, AUDIO_DIR, OUTPUTS_DIR, IMAGES_DIR, PRODUCT_IMAGES_DIR, RECOMMENDATIONS_DIR, SOURCE_MEDIA_DIR]:
    d.mkdir(parents=True, exist_ok=True)
