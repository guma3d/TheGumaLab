import json
import logging
from typing import List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, PLANNER_MODEL

logger = logging.getLogger(__name__)

class ScenePlan(BaseModel):
    scene_number: int
    duration_seconds: int = 5
    camera_movement: str
    visual_prompt: str
    narration_ko: str

class VideoStoryBoard(BaseModel):
    title: str
    summary: str
    target_aspect_ratio: str = "9:16"
    estimated_total_seconds: int
    scenes: List[ScenePlan]

def plan_video_storyboard(
    user_idea: str,
    target_duration: int = 30,
    aspect_ratio: str = "9:16",
    model_name: Optional[str] = None
) -> VideoStoryBoard:
    """Gemini API를 사용하여 사용자 아이디어를 바탕으로 30~40초 숏폼 컷씬 스토리보드를 생성합니다."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    model = model_name or PLANNER_MODEL

    num_scenes = max(4, min(8, round(target_duration / 5)))

    prompt = f"""
You are an expert AI Video Director specializing in viral short-form videos (TikTok, Reels, YouTube Shorts).
Create a complete, highly engaging video storyboard plan for the following user idea:

[User Idea / Topic]
{user_idea}

[Requirements]
- Target total duration: approximately {target_duration} seconds.
- Number of scenes: exactly {num_scenes} scenes (each scene between 4 and 6 seconds).
- Aspect ratio: {aspect_ratio} (vertical 9:16 shortform).
- For each scene:
  1. `scene_number`: 1 to {num_scenes}
  2. `duration_seconds`: 4, 5, or 6
  3. `camera_movement`: (e.g., 'Slow Dolly in', 'Fast panning right', 'Drone overhead shot', 'Low-angle tracking')
  4. `visual_prompt`: Detailed, cinematic English prompt optimized for Google Veo 3.1 video generation model. Include lighting, camera lens, subjects, atmosphere, hyperrealistic details, no text/watermarks.
  5. `narration_ko`: Natural, engaging Korean voiceover script that matches the scene timing perfectly.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoStoryBoard,
            temperature=0.7,
        ),
    )

    data = json.loads(response.text)
    return VideoStoryBoard(**data)
