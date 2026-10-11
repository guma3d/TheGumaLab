"""Run in GumaTTS after inspecting a preserved loudness-gate failure."""
import json,sys
from pathlib import Path
from audio_processing import measure
from client import submit
root=Path(sys.argv[1]);queue=json.loads((root/'promotion-v3-queue-check.json').read_text());changes={}
for index,entry in queue.items():
    folder=root/entry['id']
    if not (folder/'failure.json').exists():continue
    # Only this diagnosed failure can receive another seeded take. A model,
    # CUDA, decode, length, or peak-validation failure requires other repair.
    if not (folder/'audio.mp3').exists():raise RuntimeError('Inspect missing normalized audio: '+entry['id'])
    before=measure(folder/'original.wav');after=measure(folder/'audio.mp3')
    assert after['lufs'] < -22 and after['true_peak_dbfs']<=-1
    gain=min(-16-before['lufs'],-1.8-before['true_peak_dbfs'])
    assert abs(after['lufs']-(before['lufs']+gain))<=1
    request=json.loads((folder/'request.json').read_text())
    assert request['project']=='story' and request['model']=='qwen-design-1.7b' and request['voice']=='M5'
    assert request['seed']<46, 'Repeated failure needs further inspection'
    request['seed']+=1
    job=submit(**request)
    history=entry.get('failed_takes',[])+[dict(job_id=entry['id'],seed=entry['seed'],input=before,output=after,reason='too quiet after measured peak-safe gain')]
    changes[index]=dict(id=job['id'],seed=request['seed'],text_sha256=entry['text_sha256'],failed_takes=history)
(root/'promotion-v3-quiet-retries.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'retried_cuts':list(changes)}))
