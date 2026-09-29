import time
import logging
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, VEO_MODEL

logger = logging.getLogger(__name__)

def generate_video_clip(
    prompt: str,
    output_path: Path,
    duration_seconds: int = 5,
    aspect_ratio: str = "9:16",
    model_name: Optional[str] = None
) -> Path:
    """Google Veo 3.1 API를 호출하여 프롬프트로부터 비디오 클립을 생성하고 mp4로 저장합니다."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    model = model_name or VEO_MODEL

    logger.info(f"Generating video with model {model}: {prompt[:60]}... (duration: {duration_seconds}s)")

    operation = client.models.generate_videos(
        model=model,
        source=types.GenerateVideosSource(prompt=prompt),
        config=types.GenerateVideosConfig(
            number_of_videos=1,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            enhance_prompt=True,
        ),
    )

    # Poll operation until done
    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)

    if operation.error:
        raise RuntimeError(f"Veo generation failed: {operation.error}")

    generated_video = operation.response.generated_videos[0].video
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_video.save(str(output_path))
    logger.info(f"Video clip saved to {output_path}")

    return output_path
