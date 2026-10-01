"""승인 전에 검토할 장면별 키프레임 생성."""
from pathlib import Path
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, IMAGE_MODEL


def generate_preview_image(prompt: str, output_path: Path, aspect_ratio: str,
                           style_prompt: str, reference_path: Path | None = None,
                           product_name: str = "") -> Path:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    contents = [types.Part.from_text(text=(
        f"Create one storyboard keyframe, no text or watermarks.\n"
        f"Shared style: {style_prompt}\nScene: {prompt}\n"
        f"Product identity: {product_name or 'the supplied reference product'}.\n"
        "Create an isolated 3D mechanism concept diagram, never a complete product. "
        "The attached real photo identifies the product being explained; do NOT redraw "
        "its exterior, camera housing, enclosure, buttons or ports. The service displays "
        "the actual exterior separately from the unmodified photograph. Internal elements "
        "are conceptual mechanism illustrations, not invented exact product engineering. "
        "Ignore any conflicting request to render a complete device in the scene prompt."
    ))]
    if reference_path:
        contents.append(types.Part.from_bytes(data=reference_path.read_bytes(), mime_type="image/png"))
    # Keep the owning client alive until the request finishes. A temporary
    # Client().models chain can close its transport during garbage collection.
    with genai.Client(api_key=GEMINI_API_KEY) as client:
        response = client.models.generate_content(
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
