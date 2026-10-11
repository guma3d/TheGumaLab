"""Common synchronous client. Server retains the immutable audio and provenance."""
import hashlib
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

def request(path, data=None):
    base = os.getenv('GUMATTS_URL', 'http://host.docker.internal:8088').rstrip('/')
    token = Path(os.getenv('GUMATTS_TOKEN_FILE', '/run/secrets/gumatts_token')).read_text().strip()
    req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers={'Authorization':'Bearer '+token, 'Content-Type':'application/json'})
    for attempt in range(3 if data is None else 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:return r.read()
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, TimeoutError):
            if data is not None or attempt==2:raise
            # Repeat only the same read after a transient connection failure.
            # Failed synthesis, authorization, or model errors are not retried.
            time.sleep(attempt+1)

def submit(text, *, model=None, voice=None, style=None, project='story', title='영상 내레이션', allow_cloud=False, seed=42):
    model = model or ('qwen-clone-1.7b' if project == 'food' else 'qwen-design-1.7b')
    if voice is None:
        voice = ('M5' if project in ('story', 'longform') else 'F4') if model == 'qwen-design-1.7b' else ('Sohee' if model.startswith('qwen') else 'Zephyr')
        if model == 'qwen-clone-1.7b': voice = 'F1-bright-v2'
    payload = dict(text=text, title=title, project=project, model=model, voice=voice, allow_cloud=allow_cloud, seed=seed)
    if style is not None: payload['style'] = style
    return json.loads(request('/api/jobs', payload))

def collect(job, output_path, *, timeout=7200):
    deadline = time.monotonic() + timeout
    while job['status'] in ('queued','running'):
        if time.monotonic() > deadline:
            raise TimeoutError('GumaTTS 대기 시간 초과. 서버 작업은 보존됩니다: '+job['id'])
        time.sleep(2)
        job = json.loads(request('/api/jobs/'+job['id']))
    if job['status'] != 'ready': raise RuntimeError('GumaTTS: '+job.get('error','생성 실패'))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    downloads = []
    for kind,path in {'mp3':output, 'wav':output.with_suffix('.wav')}.items():
        raw = request(f'/media/{job["id"]}/{kind}')
        expected = job['result']['audio_sha256' if kind=='mp3' else 'original_sha256']
        if hashlib.sha256(raw).hexdigest() != expected: raise RuntimeError('음성 다운로드 해시 불일치')
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise FileExistsError(f'기존 음성을 덮어쓸 수 없습니다. 새 버전 경로를 사용하세요: {path}')
        downloads.append((path,raw))
    for path,raw in downloads:
        if not path.exists():
            temp = path.with_suffix(path.suffix+'.tmp')
            temp.write_bytes(raw)
            temp.replace(path)
    provenance = {'service':'GumaTTS', 'job_id':job['id'], 'web_url':'https://home.guma3d.com/gumatts/#job-'+job['id'], **job['result']}
    output.with_suffix('.tts.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    return provenance

def synthesize(text, output_path, *, model=None, voice=None, style=None, project='story', title='영상 내레이션', allow_cloud=False, timeout=7200, seed=42):
    job=submit(text,model=model,voice=voice,style=style,project=project,title=title,allow_cloud=allow_cloud,seed=seed)
    return collect(job,output_path,timeout=timeout)
