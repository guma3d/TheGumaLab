"""Run in VideoFactory runtime. GumaTTS is the only narration generation entrypoint."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from app.core.tts_engine import synthesize_speech

root = Path(sys.argv[1])
model = sys.argv[2] if len(sys.argv) > 2 else 'qwen-design-1.7b'
aliases = {'gemini-3.8-flash-tts':'gemini-flash', 'gemini-3.8-flash-lite-tts':'gemini-lite'}
model = aliases.get(model, model)
if model != 'qwen-design-1.7b':
    raise ValueError('GumaTTS 모델을 지정하세요.')
voice = 'M5'
script = json.loads((root/'script.json').read_text(encoding='utf-8'))
(root/'voice').mkdir(exist_ok=True)
jobs = []
for si, scene in enumerate(script['scenes'], 1):
    for pi, paragraph in enumerate(scene['narration'].split('\n\n'), 1):
        if paragraph.strip():
            jobs.append(dict(index=len(jobs)+1, scene=si, paragraph=pi, text=paragraph.strip(), file=f'voice/{len(jobs)+1:03}.mp3'))

def existing(job):
    out = root/job['file']
    marker = out.with_suffix('.json')
    if not marker.exists():
        if out.exists() and not out.with_suffix('.tts.json').exists():
            raise RuntimeError('기존 음성의 생성 기록이 없습니다. 새 버전 폴더를 사용하세요.')
        return None
    prior = json.loads(marker.read_text())
    digest = hashlib.sha256(job['text'].encode()).hexdigest()
    if prior['text_sha256'] != digest or aliases.get(prior.get('model'), prior.get('model')) != model or prior.get('voice') != voice:
        raise RuntimeError('원고·모델·음성이 다른 기존 제작본입니다. 새 버전 폴더를 사용하세요.')
    if not out.exists() or hashlib.sha256(out.read_bytes()).hexdigest() != prior['audio_sha256']:
        raise RuntimeError('기존 음성 파일이 누락되거나 변경되었습니다.')
    return prior

# Check all prior audio before changing even the job manifest or submitting work.
for job in jobs:
    existing(job)
(root/'voice-jobs.json').write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding='utf-8')

async def main():
    results = []
    for job in jobs:
        out = root/job['file']
        marker = out.with_suffix('.json')
        digest = hashlib.sha256(job['text'].encode()).hexdigest()
        prior = existing(job)
        if prior is not None:
            results.append(prior)
            continue
        await synthesize_speech(job['text'], out, voice=voice, model=model, project='story')
        provenance = json.loads(out.with_suffix('.tts.json').read_text())
        result = dict(job, duration=provenance['duration'], text_sha256=digest, voice=voice, model=model, audio_sha256=provenance['audio_sha256'], listened=False, tts_job_id=provenance['job_id'], tts_service='GumaTTS')
        marker.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        results.append(result)
        print(json.dumps({'ready':job['index'],'total':len(jobs),'seconds':round(result['duration'],2)}),flush=True)
    (root/'voice-manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'complete':len(results),'speech_seconds':sum(x['duration'] for x in results),'quality':'pending_user_listening'}),flush=True)

asyncio.run(main())
