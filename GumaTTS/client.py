"""Common synchronous client. Server retains the immutable audio and provenance."""
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

def synthesize(text, output_path, *, model='qwen-1.7b', voice='Sohee', style=None, project='story', title='영상 내레이션', allow_cloud=False, timeout=7200):
    base = os.getenv('GUMATTS_URL', 'http://host.docker.internal:8088').rstrip('/')
    token = Path(os.getenv('GUMATTS_TOKEN_FILE', '/run/secrets/gumatts_token')).read_text().strip()
    def request(path, data=None):
        req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers={'Authorization':'Bearer '+token, 'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r: return r.read()
    payload = dict(text=text, title=title, project=project, model=model, voice=voice, allow_cloud=allow_cloud)
    if style is not None: payload['style'] = style
    job = json.loads(request('/api/jobs', payload))
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
