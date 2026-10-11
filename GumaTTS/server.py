"""Authenticated, durable, single-worker narration service. Never falls back to paid APIs."""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

BASE = Path(__file__).parent
MODELS = {
    'qwen-1.7b': {'name': 'Qwen 1.7B · 품질 비교', 'repo': 'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice', 'local': True},
    'qwen-0.6b': {'name': 'Qwen 0.6B · 속도 비교', 'repo': 'Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice', 'local': True},
    'gemini-flash': {'name': 'Gemini Flash · 기존 Zephyr', 'repo': 'gemini-3.8-flash-tts', 'local': False},
    'gemini-lite': {'name': 'Gemini Lite · 외부 API', 'repo': 'gemini-3.8-flash-lite-tts', 'local': False},
}
STYLE = '자연스러운 한국어로 편안하게 이야기해주세요. 가까운 사람에게 경험을 들려주듯 따뜻하고 담백하게, 과장된 감정이나 뉴스 앵커 같은 말투 없이 읽어주세요. 문장 사이에는 짧게 쉬고, 주어진 내용만 정확히 읽어주세요.'

class Job(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(default='음성 테스트', min_length=1, max_length=120)
    project: Literal['test', 'story', 'food', 'tech', 'household', 'video'] = 'test'
    text: str = Field(min_length=1, max_length=2000)
    model: Literal['qwen-1.7b', 'qwen-0.6b', 'gemini-flash', 'gemini-lite'] = 'qwen-1.7b'
    voice: str = 'Sohee'
    style: str = Field(default=STYLE, max_length=1500)
    seed: int = Field(default=42, ge=0, le=2147483647)
    allow_cloud: bool = False

    @model_validator(mode='after')
    def valid_voice(self):
        if self.model.startswith('qwen') and self.voice != 'Sohee':
            raise ValueError('로컬 비교 음성은 Sohee를 사용합니다.')
        if self.model.startswith('gemini') and (self.voice not in ('Zephyr', 'Achird') or not self.allow_cloud):
            raise ValueError('외부 API는 음성과 비용 발생 가능성을 명시해야 합니다.')
        return self

class Review(BaseModel):
    model_config = ConfigDict(extra='forbid')
    verdict: Literal['approved', 'changes', 'pending']
    note: str = Field(default='', max_length=2000)

class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, created REAL, status TEXT, fingerprint TEXT, request TEXT, result TEXT, error TEXT, review TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, job_id TEXT, created REAL, payload TEXT)')

    def db(self):
        db = sqlite3.connect(self.root / 'jobs.sqlite3', timeout=20)
        db.row_factory = sqlite3.Row
        return db

    def get(self, jid):
        with self.db() as db:
            row = db.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if not row:
            raise HTTPException(404, '음성을 찾을 수 없습니다.')
        item = dict(row)
        for key in ('request', 'result', 'review'):
            item[key] = json.loads(item[key] or '{}')
        return item

    def create(self, job):
        data = job.model_dump()
        audio_fields = {k:data[k] for k in ('text', 'model', 'voice', 'style', 'seed')}
        audio_fields['engine_version'] = 1
        fingerprint = hashlib.sha256(json.dumps(audio_fields, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            count = db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]
            if count >= 150:
                raise HTTPException(429, '생성 대기열이 가득 찼습니다.')
            # An identical request is idempotent, including while in flight.
            prior = db.execute("SELECT id FROM jobs WHERE fingerprint=? AND request=? AND status IN ('queued','running','ready') ORDER BY created DESC LIMIT 1", (fingerprint, json.dumps(data, ensure_ascii=False))).fetchone()
            if prior:
                return self.get(prior['id'])
            jid = uuid.uuid4().hex
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)', (jid, time.time(), 'queued', fingerprint, json.dumps(data, ensure_ascii=False), '{}', '', '{}'))
        return self.get(jid)

    def work(self, stop):
        with self.db() as db:
            db.execute("UPDATE jobs SET status='failed', error='서버가 재시작되어 중단되었습니다. 원본은 보존되며 새 요청으로 재시도할 수 있습니다.' WHERE status='running'")
        while not stop.is_set():
            with self.db() as db:
                row = db.execute("SELECT id FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
                if row:
                    db.execute("UPDATE jobs SET status='running' WHERE id=?", (row['id'],))
            if not row:
                stop.wait(1)
                continue
            jid = row['id']
            folder = self.root / jid
            folder.mkdir(exist_ok=True)
            (folder / 'request.json').write_text(json.dumps(self.get(jid)['request'], ensure_ascii=False, indent=2), encoding='utf-8')
            try:
                # Process boundary guarantees VRAM is released at completion/failure.
                with (folder / 'worker.log').open('w') as log:
                    proc = subprocess.Popen([sys.executable, str(BASE / 'worker.py'), str(folder.resolve())], stdout=log, stderr=log)
                    started = time.monotonic()
                    while proc.poll() is None:
                        if stop.wait(1) or time.monotonic() - started > 3600:
                            proc.terminate()
                            try: proc.wait(timeout=10)
                            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
                            raise RuntimeError('생성 시간이 초과되었거나 서버가 종료되었습니다.')
                    if proc.returncode != 0:
                        failure = folder / 'failure.json'
                        raise RuntimeError(json.loads(failure.read_text())['error'] if failure.exists() else '모델 실행 실패. 관리자 로그를 확인해주세요.')
                result = json.loads((folder / 'result.json').read_text())
                with self.db() as db:
                    db.execute("UPDATE jobs SET status='ready', result=? WHERE id=?", (json.dumps(result, ensure_ascii=False), jid))
            except Exception as exc:
                with self.db() as db:
                    db.execute("UPDATE jobs SET status='failed', error=? WHERE id=?", (str(exc)[:500], jid))

def create_app(root=None, start_worker=True):
    store = Store(root or os.getenv('GUMATTS_STORAGE', 'storage'))
    tokenfile = store.root / 'service-token'
    if not tokenfile.exists():
        try:
            with tokenfile.open('x') as f: f.write(secrets.token_urlsafe(48))
            tokenfile.chmod(0o600)
        except FileExistsError: pass
    token = tokenfile.read_text().strip()
    stop = threading.Event()

    @asynccontextmanager
    async def lifespan(app):
        thread = threading.Thread(target=store.work, args=(stop,), daemon=True)
        if start_worker: thread.start()
        yield
        stop.set()
        if start_worker: thread.join(timeout=15)

    app = FastAPI(title='GumaTTS', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store

    @app.middleware('http')
    async def protect(request: Request, call_next):
        path = request.url.path
        prefix = '/gumatts' if request.headers.get('x-forwarded-prefix') == '/gumatts' else ''
        request.state.prefix = prefix
        machine = hmac.compare_digest(request.headers.get('authorization', ''), 'Bearer ' + token)
        if path != '/health':
            allowed = machine
            if not allowed and request.cookies.get('guma_sso_token'):
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        check = await client.get(os.getenv('GUMATTS_AUTH_URL', 'http://host.docker.internal:8081/auth'), cookies={'guma_sso_token': request.cookies['guma_sso_token']})
                        allowed = check.status_code == 200
                except httpx.HTTPError: pass
            if not allowed:
                if path.startswith(('/api/', '/media/')):
                    return JSONResponse({'detail': '홈서버 로그인이 필요합니다.'}, 401)
                target = 'https://home.guma3d.com/gumatts/'
                return RedirectResponse('https://home.guma3d.com/login?redirect_url=' + quote(target, safe=''), 302)
            if request.method not in ('GET', 'HEAD', 'OPTIONS') and not machine:
                origin = request.headers.get('origin', '')
                if request.headers.get('x-gumatts') != 'studio' or (origin and urlparse(origin).netloc != request.headers.get('host')):
                    return JSONResponse({'detail': '음성 작업실에서 다시 요청해주세요.'}, 403)
        response = await call_next(request)
        response.headers.update({'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Cache-Control': 'private, no-store', 'Referrer-Policy':'same-origin', 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"})
        return response

    app.mount('/static', StaticFiles(directory=BASE / 'static'), name='static')

    @app.get('/health')
    def health(): return {'status': 'ok', 'service': 'GumaTTS'}

    @app.get('/')
    def index(request: Request):
        return HTMLResponse((BASE / 'static/index.html').read_text(encoding='utf-8').replace('__PREFIX__', request.state.prefix))

    @app.get('/api/state')
    def state():
        with store.db() as db:
            ids = [r['id'] for r in db.execute('SELECT id FROM jobs ORDER BY created DESC LIMIT 100')]
        return {'models': MODELS, 'jobs': [store.get(i) for i in ids], 'default_style': STYLE, 'local_voice_status': '사용자 청취 검수 전 · 기본 목소리 미확정'}

    @app.post('/api/jobs', status_code=202)
    def create(job: Job): return store.create(job)

    @app.get('/api/jobs/{jid}')
    def get(jid: str): return store.get(jid)

    @app.post('/api/jobs/{jid}/review')
    def review(jid: str, review: Review):
        if store.get(jid)['status'] != 'ready': raise HTTPException(409, '생성 완료 후 청취해주세요.')
        payload = json.dumps({**review.model_dump(), 'at': time.time(), 'scope':'this_audio_only'}, ensure_ascii=False)
        with store.db() as db:
            db.execute('INSERT INTO reviews(job_id,created,payload) VALUES (?,?,?)', (jid, time.time(), payload))
            db.execute('UPDATE jobs SET review=? WHERE id=?', (payload, jid))
        return store.get(jid)

    @app.get('/media/{jid}/{kind}')
    def media(jid: str, kind: Literal['mp3', 'wav', 'manifest']):
        if store.get(jid)['status'] != 'ready': raise HTTPException(409, '아직 생성되지 않았습니다.')
        filename = {'mp3':'audio.mp3', 'wav':'original.wav', 'manifest':'result.json'}[kind]
        return FileResponse(store.root / jid / filename, media_type={'mp3':'audio/mpeg', 'wav':'audio/wav', 'manifest':'application/json'}[kind])
    return app

app = create_app()
