"""승인 전에 검토할 장면별 키프레임 생성."""
from pathlib import Path
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, IMAGE_MODEL


def generate_preview_image(prompt: str, output_path: Path, aspect_ratio: str,
                           style_prompt: str, reference_path: Path | None = None) -> Path:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    contents = [types.Part.from_text(text=(
        f"Create one storyboard keyframe, no text or watermarks.\n"
        f"Shared style: {style_prompt}\nScene: {prompt}\n"
        "If a reference image is provided, retain its palette, lighting, materials "
        "and recurring character appearance while showing the new scene."
    ))]
    if reference_path:
        contents.append(types.Part.from_bytes(data=reference_path.read_bytes(), mime_type="image/png"))
    response = genai.Client(api_key=GEMINI_API_KEY).models.generate_content(
        model=IMAGE_MODEL, contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        ),
    )
    for part in response.parts or []:
        if part.inline_data and (part.inline_data.mime_type or "").startswith("image/"):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(BytesIO(part.inline_data.data)) as image:
                image.save(output_path, format="PNG")
            return output_path
    raise RuntimeError("이미지 생성 결과가 없습니다. 모델 응답 또는 생성 제한을 확인해주세요.")
