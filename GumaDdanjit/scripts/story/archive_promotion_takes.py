"""Copy relevant rejected/superseded local takes into the story version backup."""
import hashlib,json,re,shutil,sqlite3,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();tts=Path(sys.argv[2]).resolve()
voices=json.loads((root/'voice-manifest.json').read_text(encoding='utf-8'));selected={v['tts_job_id'] for v in voices}
texts={v['text'] for v in voices}
for file in root.glob('script-v*-before-*.json'):
    for scene in json.loads(file.read_text(encoding='utf-8'))['scenes']:texts.update(scene['narration'].split('\n\n'))
records=[]
with sqlite3.connect(tts/'jobs.sqlite3') as db:rows=db.execute('SELECT id,status,request FROM jobs').fetchall()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for jid,status,payload in rows:
    req=json.loads(payload)
    if jid in selected or req['project']!='story' or req['model']!='qwen-design-1.7b' or req['voice']!='M5' or req['text'] not in texts or not re.fullmatch(r'\d{3}',req['title']):continue
    assert re.fullmatch('[a-f0-9]{32}',jid)
    folder=root/'voice/takes'/('tts-'+jid);folder.mkdir(parents=True,exist_ok=True);files=[]
    for name in ('original.wav','audio.mp3','request.json','result.json','failure.json'):
        source=tts/jid/name;target=folder/name
        if not source.exists():continue
        if target.exists():assert sha(target)==sha(source)
        else:shutil.copy2(source,target)
        files.append(dict(file=str(target.relative_to(root)),sha256=sha(target)))
    records.append(dict(job_id=jid,status=status,seed=req['seed'],cut_title=req['title'],text=req['text'],files=files,selected=False))
(root/'preserved-takes.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'preserved_rejected_or_superseded_takes':len(records)}))
