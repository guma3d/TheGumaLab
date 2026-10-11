"""All new narration is generated and archived through GumaTTS."""
import asyncio
import importlib.util
import os
from pathlib import Path
from app.config import DEFAULT_VOICE

FOOD_VOICE = 'F1-bright-v2'
FOOD_STYLE = 'Speak in natural native Korean as a bright, friendly adult female food host. Warm smiling conversational voice, lively but gentle, slightly brisk pace, short natural pauses. Not shrill, breathy, theatrical or announcer-like. Read exactly the supplied words, no additions, no laughter, no music.'
SHOPPING_VOICE = 'F4'
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
    expected = FOOD_VOICE if project == 'food' else ('M5' if project in ('story', 'longform') else 'F4')
    expected_model = 'qwen-clone-1.7b' if project == 'food' else 'qwen-design-1.7b'
    if project != 'test' and (voice != expected or model not in (None, expected_model)):
        raise ValueError('Food는 F1-bright-v2, 다른 쇼츠 F4 / Story·롱폼 M5입니다.')
    if voice == FOOD_VOICE:
        model = model or 'qwen-clone-1.7b'
        style = ''
    elif voice in ('M5', 'F4'):
        model = model or 'qwen-design-1.7b'
        style = ''  # Preserve the selected VoiceDesign profile without extra direction.
    elif voice in ('Zephyr', LEGACY_VOICE):
        model = model or 'gemini-flash'
        style = LEGACY_STYLE if voice == LEGACY_VOICE else SHOPPING_STYLE
    elif voice == 'Sohee':
        model = model or 'qwen-1.7b'
        style = None
    else:
        raise ValueError('음성 작업실에서 지원하는 목소리를 선택하세요. 자동 대체는 하지 않습니다.')
    module.synthesize(text, output_path, voice=voice, model=model, style=style, project=project, title=Path(output_path).stem, allow_cloud=model.startswith('gemini'))
    return Path(output_path)

async def synthesize_speech(text: str, output_path: Path, voice: str = DEFAULT_VOICE, rate: str = '+0%', *, model=None, project='video') -> Path:
    return await asyncio.to_thread(_gateway, text, output_path, voice, model, project)

def generate_tts_sync(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> Path:
    return asyncio.run(synthesize_speech(text, output_path, voice))
