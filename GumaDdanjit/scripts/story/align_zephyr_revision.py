"""Prepare and transcribe every selected cloud cut; run inside GumaTTS runtime."""
import hashlib,json,re,sqlite3,subprocess,sys,time,wave
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
from audio_processing import measure
root=Path(sys.argv[1]);jobs=json.loads((root/'voice-jobs.json').read_text());old=json.loads((root/'legacy-manifest.json').read_text())
if len(sys.argv)>2:jobs=[x for x in jobs if x['index'] in {int(v) for v in sys.argv[2:]}]
selection={x['index']:x for x in json.loads((root/'selected-manifest.json').read_text())} if (root/'selected-manifest.json').exists() else {}
known={x['text_sha256']:x for x in old if x['model']=='gemini-3.8-flash-tts'}
for name in ('processed','asr'): (root/name).mkdir(exist_ok=True)
model=WhisperModel('turbo',device='cpu',compute_type='int8',cpu_threads=4,download_root='/models/whisper',local_files_only=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
done=set();start=time.monotonic()
while len(done)<len(jobs):
    with sqlite3.connect('/app/storage/jobs.sqlite3') as db:
        rows=db.execute("SELECT id,request,result FROM jobs WHERE status='ready' ORDER BY created DESC").fetchall()
    for job in jobs:
        n=job['index'];out=root/'processed'/f'{n:03}.wav';dest=root/'asr'/f'{n:03}.json'
        if dest.exists():done.add(n);continue
        chosen=selection.get(n)
        if job['text_sha256'] in known and not (chosen and chosen.get('tts_job_id')):
            prior=known[job['text_sha256']];source=root/'legacy-voice'/Path(prior['file']).with_suffix('.wav').name;sourceid='promotion-v1/'+prior['file'];tts_job=None
        else:
            row=next((row for row in rows if (row[0]==chosen['tts_job_id'] if chosen and chosen.get('tts_job_id') else (lambda q:q['project']=='story' and q['model']=='gemini-flash' and q['voice']=='Zephyr' and q['title']==f'승진 v5 CUT {n:03}' and q['text']==job['text'])(json.loads(row[1])))),None)
            if row is None:continue
            tts_job=row[0];source=Path('/app/storage')/tts_job/'original.wav';sourceid=tts_job
            assert sha(source)==json.loads(row[2])['original_sha256']
        decoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-ar','48000','-ac','1','-f','s16le','-'])
        data=np.frombuffer(decoded,dtype='<i2');step=480;segments=[data[i:i+step].astype(float) for i in range(0,len(data),step)]
        rms=np.array([np.sqrt(np.mean(x*x)) for x in segments]);threshold=max(32768*10**(-48/20),float(rms.max())*10**(-35/20));active=np.flatnonzero(rms>=threshold)
        assert len(active)>0
        first=max(0,int(active[0]*step)-3840);last=min(len(data),int((active[-1]+1)*step)+6720)
        trimmed=root/'processed'/f'{n:03}-trim.wav'
        with wave.open(str(trimmed),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(data[first:last].tobytes())
        before=measure(trimmed);gain=min(-18-before['lufs'],-2.0-before['true_peak_dbfs'])
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(trimmed),'-af',f'volume={gain}dB','-c:a','pcm_s16le',str(out)],check=True,capture_output=True)
        after=measure(out);assert after['true_peak_dbfs']<=-1.5 and after['lufs']>=-23
        words=[];segs,_=model.transcribe(str(out),language='ko',beam_size=5,vad_filter=True,word_timestamps=True,condition_on_previous_text=False)
        segs=list(segs)
        for s in segs:
            words.extend(dict(text=w.word.strip(),start=w.start,end=w.end,probability=w.probability) for w in (s.words or []))
        save(dest,dict(index=n,expected=job['text'],transcript=' '.join(s.text.strip() for s in segs),words=words,audio_sha256=sha(out),source_sha256=sha(source),source=sourceid,tts_job_id=tts_job,duration=(last-first)/48000,trim_start=first/48000,trim_end=(len(data)-last)/48000,gain_db=gain,source_measurement=before,processed_measurement=after,timing_method='Whisper turbo word timestamps on processed PCM',human_listening_completed=False))
        done.add(n);print(json.dumps({'aligned':n,'ready':len(done),'total':len(jobs)}),flush=True)
    if time.monotonic()-start>10800:raise TimeoutError('Waiting for cloud cuts; resume using preserved ASR results')
    if len(done)<len(jobs):time.sleep(5)
print(json.dumps({'complete':len(done)}),flush=True)
