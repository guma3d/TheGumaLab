"""One job per process; all providers and original audio live in GumaTTS."""
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from voice_profiles import DESIGN_MODEL, DESIGN_REPO, design_instruction
from audio_processing import normalize_speech

def local_generation(request):
    """Select the correct checkpoint and API without loading a GPU model."""
    kwargs = dict(text=request['text'], language='Korean', max_new_tokens=4096)
    if request['model'] == DESIGN_MODEL:
        kwargs['instruct'] = design_instruction(request['voice'], request['style'])
        return DESIGN_REPO, 'generate_voice_design', kwargs
    size = '1.7B' if request['model'] == 'qwen-1.7b' else '0.6B'
    kwargs['speaker'] = 'Sohee'
    if size == '1.7B': kwargs['instruct'] = request['style']
    return f'Qwen/Qwen3-TTS-12Hz-{size}-CustomVoice', 'generate_custom_voice', kwargs

def run(folder):
    request = json.loads((folder / 'request.json').read_text())
    original = folder / 'original.wav'
    started = time.monotonic()
    info = {'model': request['model'], 'voice': request['voice'], 'seed': request['seed'], 'listened_to_audio': False, 'quality_status':'pending_user_listening'}
    if request['model'].startswith('qwen'):
        import torch
        import soundfile as sf
        from qwen_tts import Qwen3TTSModel
        if not torch.cuda.is_available(): raise RuntimeError('CUDA GPU를 사용할 수 없습니다.')
        repo, method, kwargs = local_generation(request)
        torch.set_num_threads(4)
        torch.manual_seed(request['seed'])
        torch.cuda.reset_peak_memory_stats()
        model = Qwen3TTSModel.from_pretrained(repo, device_map='cuda:0', dtype=torch.bfloat16, attn_implementation='sdpa')
        loaded = time.monotonic()
        with torch.inference_mode(): wavs, sr = getattr(model, method)(**kwargs)
        sf.write(str(original), wavs[0], sr, subtype='PCM_16')
        info.update(provider='local', model_repo=repo, model_revision=getattr(model.model.config, '_commit_hash', None), load_seconds=round(loaded-started,2), generation_seconds=round(time.monotonic()-loaded,2), gpu_peak_mb=round(torch.cuda.max_memory_allocated()/1024**2), gpu=torch.cuda.get_device_name(0), style_applied='instruct' in kwargs, api_charge=False)
        if request['model'] == DESIGN_MODEL: info['design_instruction'] = kwargs['instruct']
    else:
        if not request.get('allow_cloud'): raise RuntimeError('외부 API 사용이 허용되지 않았습니다.')
        model = {'gemini-flash':'gemini-3.8-flash-tts', 'gemini-lite':'gemini-3.8-flash-lite-tts'}[request['model']]
        key = os.getenv('GEMINI_API_KEY', '')
        if not key: raise RuntimeError('외부 API 키가 설정되지 않았습니다.')
        payload = {'contents':[{'role':'user','parts':[{'text':request['text'], 'speech_metadata':{'style':request['style']}}]}], 'generationConfig':{'responseModalities':['AUDIO'], 'speechConfig':{'voiceConfig':{'voice':request['voice']}}}}
        req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json', 'x-goog-api-key':key})
        try:
            with urllib.request.urlopen(req, timeout=180) as response: data = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'외부 TTS HTTP {exc.code}. 자동 재시도·유료 대체는 하지 않았습니다.') from None
        part = next(p['inlineData'] for p in data['candidates'][0]['content']['parts'] if 'inlineData' in p)
        raw = base64.b64decode(part['data'])
        if raw[:4] == b'RIFF': original.write_bytes(raw)
        else:
            with wave.open(str(original), 'wb') as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(24000); f.writeframes(raw)
        info.update(provider='gemini', model_repo=model, api_charge='depends_on_project_billing', generation_seconds=round(time.monotonic()-started,2))
    out = folder / 'audio.mp3'
    normalization = normalize_speech(original, out)
    duration = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(out)]))
    if not 0.3 < duration < 360: raise RuntimeError('음성 길이가 검수 범위를 벗어났습니다.')
    subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True,capture_output=True)
    info.update(duration=duration, elapsed_seconds=round(time.monotonic()-started,2), real_time_factor=round(info['generation_seconds']/duration,2), text_sha256=hashlib.sha256(request['text'].encode()).hexdigest(), audio_sha256=hashlib.sha256(out.read_bytes()).hexdigest(), original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(), technical_decode='passed', normalization=normalization)
    (folder / 'result.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    folder = Path(sys.argv[1])
    try: run(folder)
    except Exception as exc:
        # Keep dependency traces local; never print cloud credentials or request headers.
        import traceback
        traceback.print_exc()
        message = str(exc) if isinstance(exc, RuntimeError) and ('외부' in str(exc) or 'CUDA' in str(exc) or '길이' in str(exc)) else f'모델 실행 실패 ({type(exc).__name__}). 관리자 로그를 확인해주세요.'
        (folder/'failure.json').write_text(json.dumps({'error':message}, ensure_ascii=False), encoding='utf-8')
        sys.exit(1)
