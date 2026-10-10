"""Run inside the existing VideoFactory runtime; immutable, resumable paragraph TTS."""
import asyncio
import hashlib
import json
import subprocess
import sys
import time
import base64
import urllib.request
import wave
from pathlib import Path

from app.core.tts_engine import synthesize_speech
from app.core.tts_engine import SHOPPING_STYLE
from app.config import GEMINI_API_KEY

root = Path(sys.argv[1])
model = sys.argv[2] if len(sys.argv)>2 else 'gemini-3.8-flash-tts'
def alternate_speech(text, output):
    payload={'contents':[{'role':'user','parts':[{'text':text,'speech_metadata':{'style':SHOPPING_STYLE}}]}],
        'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'voice':'Zephyr'}}}}
    req=urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':GEMINI_API_KEY})
    with urllib.request.urlopen(req,timeout=120) as response:result=json.load(response)
    part=next(p['inlineData'] for p in result['candidates'][0]['content']['parts'] if 'inlineData' in p)
    raw=base64.b64decode(part['data']);wav=output.with_suffix('.wav')
    if raw[:4]==b'RIFF':wav.write_bytes(raw)
    else:
        with wave.open(str(wav),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(raw)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-b:a','192k',str(output)],check=True,capture_output=True)
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
    sem=asyncio.Semaphore(1)
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
            for attempt in range(1,9):
                try:
                    async with gate:
                        await asyncio.sleep(max(0, 10-(time.monotonic()-last_started)))
                        last_started=time.monotonic()
                    if model=='gemini-3.8-flash-tts':await synthesize_speech(job['text'],out,voice='Zephyr')
                    else:await asyncio.to_thread(alternate_speech,job['text'],out)
                    duration=probe(out)
                    if not 0.6<duration<90: raise ValueError('Unexpected speech length')
                    result=dict(job,duration=duration,text_sha256=digest,voice='Zephyr',model=model,attempt=attempt,audio_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),listened=False)
                    marker.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
                    print(json.dumps({'ready':job['index'],'total':len(jobs),'seconds':round(duration,2)}),flush=True)
                    return result
                except Exception as exc:
                    status=getattr(exc,'code',None)
                    limits=[]
                    if status==429:
                        try:
                            error=json.load(exc).get('error',{})
                            limits=[{k:v for k,v in x.items() if k in ('quotaMetric','quotaId','quotaValue')} for t in error.get('details',[]) for x in t.get('violations',[])]
                        except Exception:pass
                    print(json.dumps({'retry':job['index'],'attempt':attempt,'error_type':type(exc).__name__,'http_status':status,'limits':limits}),flush=True)
                    if any('PerDay' in x.get('quotaId','') for x in limits):
                        raise RuntimeError('Daily TTS model quota exhausted; preserve completed paragraphs and select an available model.') from None
                    if attempt==8:raise RuntimeError(f'TTS block {job["index"]} failed') from None
                    await asyncio.sleep(60 if status==429 else 8*attempt)
    results=await asyncio.gather(*(run(j) for j in jobs))
    (root/'voice-manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'complete':len(results),'speech_seconds':sum(x['duration'] for x in results)}),flush=True)
asyncio.run(main())
