"""Generate an immutable, per-cut CustomVoice comparison through GumaTTS."""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
parent=root.parent/'promotion-v4'
root.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('tts_client','/opt/gumatts/client.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
style=('Warm, friendly conversational Korean narration, as a confident host explaining an interesting social issue to a friend. '
       'Clear pronunciation, a comfortable steady pace, gentle emphasis on important words and natural pauses. '
       'Maintain a consistent natural vocal register and full voice throughout. '
       'Avoid whispering, exaggerated high pitches, sing-song delivery and overacting. Read only the supplied text.')
settings=dict(model='qwen-1.7b',voice='Sohee',style=style,project='test',seed=42,
              source_video='promotion-film-v4',source_script_version=9,cut_count=31,
              scope='First 31 cuts including source cut 028; experimental, not a production voice policy change')
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
settings_path=root/'voice-settings.json'
if settings_path.exists():assert json.loads(settings_path.read_text())==settings
else:save(settings_path,settings)
source=json.loads((parent/'voice-manifest.json').read_text())[:31]
script=json.loads((parent/'script.json').read_text());save(root/'script.json',script)
jobs=[dict(index=p['index'],scene=p['scene'],paragraph=p['paragraph'],text=p['text'],
           cut_id=p['cut_id'],text_sha256=p['text_sha256'],file=f"voice/{p['index']:03}.mp3") for p in source]
save(root/'voice-jobs.json',jobs)
queue_path=root/'voice-queue.json';queue=json.loads(queue_path.read_text()) if queue_path.exists() else {}
for job in jobs:
 key=str(job['index'])
 if key not in queue:
  service=client.submit(job['text'],model=settings['model'],voice='Sohee',style=style,project='test',
                        title=f"GumaStory Sohee friendly v1 CUT {job['index']:03}",seed=42)
  queue[key]=[dict(id=service['id'],seed=42)];save(queue_path,queue)
print(json.dumps(dict(queued=len(queue),model=settings['model'],voice='Sohee')),flush=True)
manifest=[]
for job in jobs:
 key=str(job['index']);out=root/job['file'];mark=out.with_suffix('.json')
 if mark.exists():
  record=json.loads(mark.read_text());meta=json.loads(out.with_suffix('.tts.json').read_text())
  assert record['text_sha256']==job['text_sha256'] and sha(out)==record['audio_sha256']
  assert meta['model']=='qwen-1.7b' and meta['voice']=='Sohee' and meta['style_applied']
  assert sha(out.with_suffix('.wav'))==meta['original_sha256']
  manifest.append(record);continue
 for attempt in range(3):
  if attempt>=len(queue[key]):
   seed=42+attempt
   s=client.submit(job['text'],model='qwen-1.7b',voice='Sohee',style=style,project='test',
                  title=f"GumaStory Sohee friendly v1 CUT {job['index']:03}",seed=seed)
   queue[key].append(dict(id=s['id'],seed=seed));save(queue_path,queue)
  entry=queue[key][attempt];s=json.loads(client.request('/api/jobs/'+entry['id']))
  take=root/f"takes/{job['index']:03}-{entry['seed']}/audio.mp3"
  try:meta=client.collect(s,take)
  except RuntimeError as exc:
   entry['failure']=str(exc);save(queue_path,queue)
   print(json.dumps(dict(failed=job['index'],seed=entry['seed'],error=str(exc))),flush=True)
   continue
  assert meta['provider']=='local' and meta['voice']=='Sohee' and meta['style_applied'] and not meta['api_charge']
  out.parent.mkdir(exist_ok=True)
  for suffix in ('.mp3','.wav','.tts.json'):shutil.copy2(take.with_suffix(suffix),out.with_suffix(suffix))
  record=dict(job,model='qwen-1.7b',voice='Sohee',style=style,seed=entry['seed'],
              duration=meta['duration'],audio_sha256=meta['audio_sha256'],tts_job_id=meta['job_id'],
              tts_service='GumaTTS',listened=False)
  save(mark,record);manifest.append(record)
  print(json.dumps(dict(ready=job['index'],total=len(jobs),seconds=meta['duration'])),flush=True)
  break
 else:raise RuntimeError(f"Cut {job['index']} failed three preserved takes")
save(root/'voice-manifest.json',manifest)
print(json.dumps(dict(complete=len(manifest),speech_seconds=sum(p['duration'] for p in manifest))),flush=True)
