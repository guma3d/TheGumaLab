"""CPU transcription of GumaTTS results; keep separate from human listening."""
import hashlib,json,re,sqlite3,sys,time
from pathlib import Path
from difflib import SequenceMatcher
from faster_whisper import WhisperModel

root=Path(sys.argv[1]);jobs=json.loads((root/'voice-jobs.json').read_text())
tts=root.parent;out=root/'asr.json'
rows=json.loads(out.read_text()) if out.exists() else []
model=WhisperModel('turbo',device='cpu',compute_type='int8',cpu_threads=2,download_root='/models/whisper',local_files_only=True)
def norm(s):return re.sub(r'[^가-힣a-zA-Z0-9]','',s).lower()
deadline=time.monotonic()+14400
for job in jobs:
    if any(r['index']==job['index'] for r in rows):continue
    while True:
        with sqlite3.connect(tts/'jobs.sqlite3') as db:
            candidates=db.execute("SELECT id,request,result FROM jobs WHERE status='ready' ORDER BY created DESC").fetchall()
        selected=next((r for r in candidates if (lambda q:q['project']=='story' and q['model']=='qwen-design-1.7b' and q['voice']=='M5' and q['title']==f"{job['index']:03}" and q['text']==job['text'])(json.loads(r[1]))),None)
        if selected:break
        if time.monotonic()>deadline:raise TimeoutError('Audio generation not finished; audit can resume.')
        time.sleep(5)
    jid,request,result=selected;file=tts/jid/'audio.mp3';result=json.loads(result)
    assert hashlib.sha256(file.read_bytes()).hexdigest()==result['audio_sha256']
    segments,_=model.transcribe(str(file),language='ko',beam_size=5,vad_filter=True,word_timestamps=True)
    segments=list(segments);transcript=' '.join(s.text.strip() for s in segments)
    rows.append(dict(index=job['index'],job_id=jid,audio_sha256=result['audio_sha256'],expected=job['text'],transcript=transcript,
        similarity=SequenceMatcher(None,norm(job['text']),norm(transcript)).ratio(),segments=[dict(start=s.start,end=s.end,text=s.text) for s in segments],human_listening_completed=False))
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'audited':job['index'],'similarity':round(rows[-1]['similarity'],3)}),flush=True)
