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
    duration_seconds: int = 4
    camera_movement: str
    visual_prompt: str
    narration_ko: str
    image_url: Optional[str] = None

class VideoStoryBoard(BaseModel):
    title: str
    summary: str
    target_aspect_ratio: str = "9:16"
    estimated_total_seconds: int
    scenes: List[ScenePlan]

def plan_video_storyboard(
    user_idea: str,
    target_duration: int = 20,
    aspect_ratio: str = "9:16",
    model_name: Optional[str] = None,
    scene_count: int = 6,
    style_prompt: str = "Cinematic realistic imagery, consistent warm lighting and restrained colors",
) -> VideoStoryBoard:
    """Gemini API를 사용하여 사용자 아이디어를 바탕으로 숏폼 컷씬 스토리보드를 생성합니다."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    model = model_name or PLANNER_MODEL

    num_scenes = scene_count

    prompt = f"""
You are an expert AI Video Director specializing in viral short-form videos (TikTok, Reels, YouTube Shorts).
Create a complete, highly engaging video storyboard plan for the following user idea:

[User Idea / Topic]
{user_idea}

[Requirements]
- Shared visual style for ALL scenes: {style_prompt}
- Maintain the same palette, lighting, character appearance, materials and visual language across all scenes.
- Target total duration: approximately {target_duration} seconds.
- Number of scenes: exactly {num_scenes} scenes.
- Aspect ratio: {aspect_ratio} (vertical 9:16 shortform).
- For each scene:
  1. `scene_number`: 1 to {num_scenes}
  2. `duration_seconds`: exactly 4 (Google Veo standard)
  3. `camera_movement`: (e.g., 'Slow Dolly in', 'Fast panning right', 'Drone overhead shot', 'Low-angle tracking')
  4. `visual_prompt`: Detailed English prompt for a still keyframe and its subsequent animation. Follow the shared visual style, describe subjects, composition and lighting, no text/watermarks. Do not impose realism if the shared style calls for illustration or animation.
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
    storyboard = VideoStoryBoard(**data)
    if len(storyboard.scenes) != num_scenes:
        raise ValueError("기획된 컷 수가 요청한 컷 수와 다릅니다. 다시 시도해주세요.")
    for index, scene in enumerate(storyboard.scenes, 1):
        scene.scene_number = index
        scene.duration_seconds = 4
        scene.image_url = None
    storyboard.target_aspect_ratio = aspect_ratio
    storyboard.estimated_total_seconds = num_scenes * 4
    return storyboard
