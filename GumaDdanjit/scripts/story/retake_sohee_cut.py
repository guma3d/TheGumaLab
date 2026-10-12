"""Preserve a bounded set of paced CustomVoice candidates for one reported cut."""
import importlib.util
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
assert not (root/'publication.json').exists(), 'Published versions are immutable'
spec = importlib.util.spec_from_file_location('tts_client', '/opt/gumatts/client.py')
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)
source = json.loads((root/'source-cut010.json').read_text())
settings = json.loads((root/'source-voice-settings.json').read_text())
style = settings['style'] + (' Keep a brisk but unhurried, even conversational rhythm. '
    'Pronounce short words briefly; do not stretch vowels or draw out word endings. '
    'Use brief natural sentence pauses. Avoid dramatic pauses and sudden slowing within a sentence.')
queue = root/'retake-queue.json'
jobs = json.loads(queue.read_text()) if queue.exists() else []
if not jobs:
    for seed in (42,43,44):
        job = client.submit(source['text'], model='qwen-1.7b', voice='Sohee', style=style,
            project='test', title=f'GumaStory Sohee pace v2 CUT 010 take {seed}', seed=seed)
        jobs.append(dict(id=job['id'],seed=seed))
        queue.write_text(json.dumps(jobs,ensure_ascii=False,indent=2))
for job in jobs:
    output = root/f"takes/{job['seed']}/audio.mp3"
    if output.with_suffix('.tts.json').exists():
        continue
    try:
        meta = client.collect(json.loads(client.request('/api/jobs/'+job['id'])),output)
        assert meta['provider']=='local' and meta['voice']=='Sohee' and meta['style_applied']
        job['result']=meta
    except RuntimeError as exc:
        job['failure']=str(exc)
    queue.write_text(json.dumps(jobs,ensure_ascii=False,indent=2))
    print(json.dumps(dict(seed=job['seed'],ready='result' in job),ensure_ascii=False),flush=True)
(root/'retake-settings.json').write_text(json.dumps(dict(model='qwen-1.7b',voice='Sohee',
    style=style,project='test',pitch_changed=False,speed_changed=False,source_index=10,
    text=source['text'],human_listening_completed=False),ensure_ascii=False,indent=2))
