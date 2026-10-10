"""Run inside the existing VideoFactory runtime; immutable, resumable paragraph TTS."""
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from app.core.tts_engine import synthesize_speech

root = Path(sys.argv[1])
script = json.loads((root/'script.json').read_text(encoding='utf-8'))
(root/'voice').mkdir(exist_ok=True)
jobs=[]
for si,scene in enumerate(script['scenes'],1):
    for pi,paragraph in enumerate(scene['narration'].split('\n\n'),1):
        if paragraph.strip():
            jobs.append(dict(index=len(jobs)+1,scene=si,paragraph=pi,text=paragraph.strip(),file=f'voice/{len(jobs)+1:03}.mp3'))
(root/'voice-jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
def probe(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    assert any(s['codec_type']=='audio' for s in data['streams'])
    return float(data['format']['duration'])
async def main():
    sem=asyncio.Semaphore(2)
    gate=asyncio.Lock()
    last_started=0.0
    async def run(job):
        nonlocal last_started
        async with sem:
            out=root/job['file']; marker=out.with_suffix('.json')
            digest=hashlib.sha256(job['text'].encode()).hexdigest()
            if marker.exists():
                prior=json.loads(marker.read_text()); assert prior['text_sha256']==digest
                return prior
            for attempt in range(1,7):
                try:
                    async with gate:
                        await asyncio.sleep(max(0, 7-(time.monotonic()-last_started)))
                        last_started=time.monotonic()
                    await synthesize_speech(job['text'],out,voice='Zephyr')
                    duration=probe(out)
                    if not 0.6<duration<90: raise ValueError('Unexpected speech length')
                    result=dict(job,duration=duration,text_sha256=digest,voice='Zephyr',model='gemini-3.8-flash-tts',attempt=attempt,audio_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),listened=False)
                    marker.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
                    print(json.dumps({'ready':job['index'],'total':len(jobs),'seconds':round(duration,2)}),flush=True)
                    return result
                except Exception as exc:
                    status=getattr(exc,'code',None)
                    print(json.dumps({'retry':job['index'],'attempt':attempt,'error_type':type(exc).__name__,'http_status':status}),flush=True)
                    if attempt==6:raise RuntimeError(f'TTS block {job["index"]} failed') from None
                    await asyncio.sleep(30 if status==429 else 8*attempt)
    results=await asyncio.gather(*(run(j) for j in jobs))
    (root/'voice-manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'complete':len(results),'speech_seconds':sum(x['duration'] for x in results)}),flush=True)
asyncio.run(main())
