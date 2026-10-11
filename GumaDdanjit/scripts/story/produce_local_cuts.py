"""Durable per-cut local M5 jobs; reuse unchanged verified audio across revisions."""
import hashlib,importlib.util,json,shutil,sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
spec=importlib.util.spec_from_file_location('gumatts_client','/opt/gumatts/client.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
settings=json.loads((root/'voice-settings.json').read_text()) if (root/'voice-settings.json').exists() else dict(model='qwen-design-1.7b',voice='M5')
model=settings['model'];voice=settings['voice']
profile=json.loads(client.request('/api/state'))['voice_profiles'][voice]['instruct'] if model=='qwen-design-1.7b' else None
def matches(meta):
    return meta.get('design_instruction','').startswith(profile+' ') if profile else (meta.get('reference_sha256')==settings['reference_sha256'] and (not settings.get('model_revision') or meta.get('model_revision')==settings['model_revision']) and (not settings.get('reference_text_sha256') or meta.get('reference_text_sha256')==settings['reference_text_sha256']))
script=json.loads((root/'script.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
jobs=[]
for si,scene in enumerate(script['scenes'],1):
    for pi,text in enumerate(scene['narration'].split('\n\n'),1):
        if text.strip():
            n=len(jobs)+1
            jobs.append(dict(index=n,scene=si,paragraph=pi,text=text.strip(),file=f'voice/{n:03}.mp3',cut_id=hashlib.sha256(text.strip().encode()).hexdigest()))
(root/'voice').mkdir(exist_ok=True);save(root/'voice-jobs.json',jobs)
def prior(job):
    out=root/job['file'];mark=out.with_suffix('.json')
    if not mark.exists():return None
    data=json.loads(mark.read_text());provenance=json.loads(out.with_suffix('.tts.json').read_text())
    assert data['text_sha256']==job['cut_id'] and data['model']==model and data['voice']==voice
    assert provenance['provider']=='local' and not provenance['api_charge']
    assert matches(provenance), 'Selected M5 profile changed; prepare a new take.'
    assert sha(out)==data['audio_sha256'] and sha(out.with_suffix('.wav'))==provenance['original_sha256']
    return data

# A changed cut order must not imply a changed voice cache key.
cache={}
for folder in root.parent.iterdir():
    if folder==root or not folder.is_dir():continue
    reviewed=folder/'production-review.json'
    if not reviewed.exists():continue
    quality=json.loads(reviewed.read_text()).get('asr_review',{})
    if quality.get('meaningful_mismatches')!=0 or not quality.get('cut_count'):continue
    for mark in (folder/'voice').glob('*.json'):
        if mark.name.endswith('.tts.json'):continue
        data=json.loads(mark.read_text())
        if data.get('model')!=model or data.get('voice')!=voice:continue
        source=mark.with_suffix('.mp3');prov=source.with_suffix('.tts.json')
        if source.exists() and source.with_suffix('.wav').exists() and prov.exists() and sha(source)==data.get('audio_sha256'):
            meta=json.loads(prov.read_text())
            settings=json.loads(client.request('/api/jobs/'+data['tts_job_id']))['request']
            if settings['style']=='' and meta.get('provider')=='local' and meta.get('normalization',{}).get('passed') and matches(meta) and sha(source.with_suffix('.wav'))==meta['original_sha256']:
                cache.setdefault(data['text_sha256'],(source,data))
for job in jobs:
    if prior(job):continue
    if job['cut_id'] in cache:
        source,data=cache[job['cut_id']];out=root/job['file']
        assert not out.exists()
        for suffix in ('.mp3','.wav','.tts.json'):shutil.copy2(source.with_suffix(suffix),out.with_suffix(suffix))
        save(out.with_suffix('.json'),dict(data,**job,reused_from=str(source)))

queuefile=root/'voice-queue.json';queue=json.loads(queuefile.read_text()) if queuefile.exists() else {}
# Cut 002's first seed had excessive crest factor and failed the service gate.
# A new seed is a separate preserved take, not a waiver of that gate.
selected={1,5,20,43,80,109} if '--pilot' in sys.argv else {j['index'] for j in jobs}
for job in jobs:
    if job['index'] not in selected or prior(job):continue
    key=str(job['index'])
    if key not in queue:
        seed=42
        submitted=client.submit(job['text'],model=model,voice=voice,project='story',title=f"{job['index']:03}",seed=seed)
        queue[key]=dict(id=submitted['id'],seed=seed,text_sha256=job['cut_id'])
        save(queuefile,queue)
print(json.dumps({'queued':len(queue),'cached':sum(prior(j) is not None for j in jobs)}),flush=True)
results=[];failures=[]
for job in jobs:
    if job['index'] not in selected:continue
    old=prior(job)
    if old:results.append(old);continue
    entry=queue[str(job['index'])]
    assert entry['text_sha256']==job['cut_id']
    service=json.loads(client.request('/api/jobs/'+entry['id']))
    out=root/job['file']
    try:provenance=client.collect(service,out)
    except RuntimeError as exc:
        failures.append(dict(index=job['index'],job_id=entry['id'],error=str(exc)))
        save(root/'voice-failures.json',failures);print(json.dumps({'failed':job['index']}),flush=True);continue
    result=dict(job,duration=provenance['duration'],text_sha256=job['cut_id'],voice=voice,model=model,audio_sha256=provenance['audio_sha256'],listened=False,tts_job_id=provenance['job_id'],tts_service='GumaTTS',seed=provenance['seed'])
    save(out.with_suffix('.json'),result);results.append(result)
    print(json.dumps({'ready':job['index'],'total':len(jobs),'seconds':round(result['duration'],2)}),flush=True)
if failures:raise SystemExit(f'{len(failures)} preserved failed takes require inspection; completed cuts are reusable.')
save(root/'voice-manifest.json',results)
print(json.dumps({'complete':len(results),'speech_seconds':sum(r['duration'] for r in results)}),flush=True)
