import asyncio
import logging
from pathlib import Path
import edge_tts
from app.config import DEFAULT_VOICE

logger = logging.getLogger(__name__)

SHOPPING_VOICE = 'Achird'
SHOPPING_STYLE = 'Speak in natural native Korean, warm, cheerful, affectionate and approachable adult male shopping host. Smile in the voice, conversational not announcer-like, slightly brisk pace, short natural pauses, clear consonants. Read exactly the supplied words, no additions, no laughter, no music.'

def _achird(text, output_path):
    import base64, json, urllib.request, wave, subprocess
    from app.config import GEMINI_API_KEY
    payload={'contents':[{'role':'user','parts':[{'text':text,'speech_metadata':{'style':SHOPPING_STYLE}}]}],
             'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'voice':SHOPPING_VOICE}}}}
    req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent',
        data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':GEMINI_API_KEY})
    with urllib.request.urlopen(req,timeout=120) as response: result=json.load(response)
    part=next(p['inlineData'] for p in result['candidates'][0]['content']['parts'] if 'inlineData' in p)
    raw=base64.b64decode(part['data']);wav=output_path.with_suffix('.wav')
    if raw[:4]==b'RIFF':wav.write_bytes(raw)
    else:
        with wave.open(str(wav),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(raw)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-b:a','192k',str(output_path)],check=True,capture_output=True)
    return output_path

async def synthesize_speech(
    text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE,
    rate: str = '+0%'
) -> Path:
    """Edge-TTS를 사용하여 한국어 텍스트를 mp3 음성 파일로 생성합니다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if voice == SHOPPING_VOICE:
        return await asyncio.to_thread(_achird,text,output_path)
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(output_path))
    logger.info(f"Synthesized TTS audio saved to {output_path}")
    return output_path

def generate_tts_sync(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> Path:
    """동기 환경에서 호출하기 위한 래퍼 함수"""
    return asyncio.run(synthesize_speech(text, output_path, voice))
