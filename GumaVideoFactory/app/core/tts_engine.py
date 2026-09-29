import asyncio
import logging
from pathlib import Path
import edge_tts
from app.config import DEFAULT_VOICE

logger = logging.getLogger(__name__)

async def synthesize_speech(
    text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE
) -> Path:
    """Edge-TTS를 사용하여 한국어 텍스트를 mp3 음성 파일로 생성합니다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    logger.info(f"Synthesized TTS audio saved to {output_path}")
    return output_path

def generate_tts_sync(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> Path:
    """동기 환경에서 호출하기 위한 래퍼 함수"""
    return asyncio.run(synthesize_speech(text, output_path, voice))
