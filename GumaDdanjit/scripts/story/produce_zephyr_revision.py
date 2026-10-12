"""Immutable Story revision: reuse exact approved Flash/Zephyr originals, generate changed cuts only."""
import hashlib, importlib.util, json, shutil, sys, time
from pathlib import Path
root=Path(sys.argv[1]); parent=root.parent/'promotion-v1'
spec=importlib.util.spec_from_file_location('tts_client','/opt/gumatts/client.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
STYLE='Speak in natural native Korean as a bright, friendly adult female food host. Warm smiling conversational voice, lively but gentle, slightly brisk pace, short natural pauses. Not shrill, breathy, theatrical or announcer-like. Read exactly the supplied words, no additions, no laughter, no music.'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
script=json.loads((root/'script.json').read_text()); old=json.loads((parent/'voice-manifest.json').read_text())
reuse={x['text_sha256']:x for x in old if x['model']=='gemini-3.8-flash-tts' and x['voice']=='Zephyr'}
jobs=[]
for si,sc in enumerate(script['scenes'],1):
    for pi,t in enumerate(sc['narration'].split('\n\n'),1):
        if t.strip():jobs.append(dict(index=len(jobs)+1,scene=si,paragraph=pi,text=t.strip(),file=f'voice/{len(jobs)+1:03}.mp3',text_sha256=hashlib.sha256(t.strip().encode()).hexdigest()))
(root/'voice').mkdir(exist_ok=True);save(root/'voice-jobs.json',jobs)
save(root/'voice-settings.json',dict(model='gemini-flash',model_repo='gemini-3.8-flash-tts',voice='Zephyr',style=STYLE,allow_cloud=True,seed=42,legacy_reuse='exact narration hashes from promotion-v1 Flash only',automatic_model_fallback=False))
results=[]
for job in jobs:
    out=root/job['file'];marker=out.with_suffix('.json')
    if marker.exists():
        result=json.loads(marker.read_text());assert result['text_sha256']==job['text_sha256'] and result['audio_sha256']==sha(out)
    elif job['text_sha256'] in reuse:
        prior=reuse[job['text_sha256']];source=parent/prior['file'];assert sha(source)==prior['audio_sha256']
        for ext in ('.mp3','.wav'):shutil.copy2(source.with_suffix(ext),out.with_suffix(ext))
        result=dict(job,model='gemini-flash',model_repo='gemini-3.8-flash-tts',voice='Zephyr',duration=prior['duration'],audio_sha256=sha(out),original_sha256=sha(out.with_suffix('.wav')),reuse_source=f'promotion-v1/{prior["file"]}',reuse_source_index=prior['index'],tts_job_id=None,provider='gemini',listened=False)
        save(marker,result)
    else:
        pending=out.with_suffix('.request.json')
        if pending.exists():remote=json.loads(client.request('/api/jobs/'+json.loads(pending.read_text())['job_id']))
        else:
            remote=client.submit(job['text'],model='gemini-flash',voice='Zephyr',style=STYLE,project='story',title=f'승진 v5 CUT {job["index"]:03}',allow_cloud=True)
            save(pending,dict(job_id=remote['id'],request_hash=job['text_sha256'],model='gemini-flash',voice='Zephyr',created=time.time()))
        try:meta=client.collect(remote,out)
        except Exception as e:
            save(root/'voice-failure.json',dict(index=job['index'],job_id=remote['id'],error=str(e),automatic_model_fallback=False));raise
        assert meta['provider']=='gemini' and meta['model_repo']=='gemini-3.8-flash-tts'
        result=dict(job,model='gemini-flash',model_repo=meta['model_repo'],voice='Zephyr',duration=meta['duration'],audio_sha256=sha(out),original_sha256=sha(out.with_suffix('.wav')),tts_job_id=meta['job_id'],provider='gemini',listened=False,reuse_source=None)
        save(marker,result)
        time.sleep(10)
    results.append(result);save(root/'voice-manifest.json',results)
    print(json.dumps({'ready':job['index'],'total':len(jobs),'reused':bool(result.get('reuse_source')),'seconds':result['duration']}),flush=True)
save(root/'voice-production.json',dict(complete=len(results),reused=sum(bool(x.get('reuse_source')) for x in results),new=sum(not x.get('reuse_source') for x in results),script_sha256=sha(root/'script.json'),model='gemini-3.8-flash-tts',voice='Zephyr',human_listening_completed=False))
