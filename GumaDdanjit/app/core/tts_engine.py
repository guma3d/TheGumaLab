"""All new narration is generated and archived through GumaTTS."""
import asyncio
import importlib.util
import os
from pathlib import Path
from app.config import DEFAULT_VOICE

FOOD_VOICE = 'Sohee'
FOOD_STYLE = 'Speak in natural native Korean as a bright, friendly adult female food host. Warm smiling conversational voice, lively but gentle, slightly brisk pace, short natural pauses. Not shrill, breathy, theatrical or announcer-like. Read exactly the supplied words, no additions, no laughter, no music.'
SHOPPING_VOICE = 'Sohee'
SHOPPING_STYLE = FOOD_STYLE
LEGACY_VOICE = 'Achird'
LEGACY_STYLE = 'Speak in natural native Korean, warm, cheerful, affectionate and approachable adult male shopping host. Smile in the voice, conversational not announcer-like, slightly brisk pace, short natural pauses, clear consonants. Read exactly the supplied words, no additions, no laughter, no music.'

def _gateway(text, output_path, voice, model=None, project='video'):
    source = Path(os.getenv('GUMATTS_CLIENT_PATH', '/opt/gumatts/client.py'))
    if not source.exists():
        source = Path(__file__).resolve().parents[3] / 'GumaTTS' / 'client.py'
    spec = importlib.util.spec_from_file_location('gumatts_client', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if project in ('story', 'longform'):
        if voice != 'Zephyr' or model not in (None, 'gemini-flash'):
            raise ValueError('Story 롱폼은 Gemini Flash / Zephyr만 사용합니다.')
        model = 'gemini-flash'
    else:
        if voice != 'Sohee' or model not in (None, 'qwen-1.7b'):
            raise ValueError('쇼핑 제작은 qwen-1.7b / Sohee만 사용합니다.')
        model = 'qwen-1.7b'
    style = None  # Service supplies one consistent Korean direction.
    module.synthesize(text, output_path, voice=voice, model=model, style=style, project=project, title=Path(output_path).stem, allow_cloud=model.startswith('gemini'))
    return Path(output_path)

async def synthesize_speech(text: str, output_path: Path, voice: str = DEFAULT_VOICE, rate: str = '+0%', *, model=None, project='video') -> Path:
    return await asyncio.to_thread(_gateway, text, output_path, voice, model, project)

def generate_tts_sync(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> Path:
    return asyncio.run(synthesize_speech(text, output_path, voice))
