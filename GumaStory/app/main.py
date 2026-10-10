import json
import os
import re
import subprocess
import uuid
from html import escape
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlparse

import httpx
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.store import Store, seed_script

BASE = Path(__file__).parent
SEED = json.loads((BASE.parent / 'seed.json').read_text(encoding='utf-8'))
CHAR_IDS = {c['id'] for c in SEED['characters']}


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class AssetReview(Model):
    revision: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    status: Literal['review', 'approved', 'changes']
    note: str = Field(default='', max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=30)
    archived: bool = False


class Scene(Model):
    start: int = Field(ge=0, le=36000)
    end: int = Field(gt=0, le=36000)
    title: str = Field(min_length=1, max_length=160)
    narration: str = Field(default='', max_length=30000)
    visual: str = Field(default='', max_length=6000)
    source: str = Field(default='', max_length=6000)
    asset_ids: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode='after')
    def duration(self):
        if self.end <= self.start:
            raise ValueError('종료 시간은 시작 시간 이후여야 합니다.')
        return self


class Script(Model):
    expected_version: int = Field(ge=0)
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default='', max_length=5000)
    status: Literal['outline', 'draft', 'review', 'approved'] = 'draft'
    note: str = Field(default='', max_length=5000)
    scenes: list[Scene] = Field(default_factory=list, max_length=100)

    @model_validator(mode='after')
    def timeline(self):
        previous = 0
        for scene in self.scenes:
            if scene.start < previous:
                raise ValueError('구간은 시간순이며 서로 겹치지 않아야 합니다.')
            previous = scene.end
        return self


class Profile(Model):
    name: str = Field(min_length=1, max_length=80)
    notes: str = Field(default='', max_length=5000)
    master_id: str = Field(default='', max_length=120)


def create_app(storage=None, testing=False):
    app = FastAPI(title='GumaStory', docs_url=None, redoc_url=None, openapi_url=None)
    store = Store(storage or os.getenv('GUMASTORY_STORAGE', 'storage'))
    seed_script(store)
    app.state.store = store

    @app.middleware('http')
    async def protect(request: Request, call_next):
        path = request.url.path
        prefix = '/gumastory' if request.headers.get('x-forwarded-prefix') == '/gumastory' else ''
        request.state.prefix = prefix
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            if request.headers.get('x-gumastory') != 'studio' or (origin and urlparse(origin).netloc != request.headers.get('host')):
                return JSONResponse({'detail': '작업실에서 다시 요청해주세요.'}, 403)
        if path != '/health' and not testing:
            cookie = request.cookies.get('guma_sso_token')
            allowed = False
            if cookie:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        auth = await client.get(os.getenv('GUMASTORY_AUTH_URL', 'http://host.docker.internal:8081/auth'), cookies={'guma_sso_token': cookie})
                        allowed = auth.status_code == 200
                except httpx.HTTPError:
                    pass
            if not allowed:
                if path.startswith('/api/') or path.startswith('/media/'):
                    return JSONResponse({'detail': '홈서버 로그인이 필요합니다.'}, 401)
                target = ('https://home.guma3d.com' + prefix if prefix else 'https://gumastory.guma3d.com') + path
                if request.url.query:
                    target += '?' + request.url.query
                return RedirectResponse('https://home.guma3d.com/login?redirect_url=' + quote(target, safe=''), 302)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control'] = 'private, no-store'
        return response

    app.mount('/static', StaticFiles(directory=BASE / 'static'), name='static')

    @app.get('/health')
    def health():
        with store.connect() as db:
            db.execute('SELECT 1')
        return {'status': 'ok', 'service': 'GumaStory'}

    @app.get('/')
    def index(request: Request):
        html = (BASE / 'static' / 'index.html').read_text(encoding='utf-8')
        return HTMLResponse(html.replace('__PREFIX__', request.state.prefix))

    @app.get('/api/state')
    def state():
        store.ingest()
        chars = [dict(c, **store.profile(c['id'])) for c in SEED['characters']]
        return {'characters': chars, 'assets': store.assets(), 'scripts': store.scripts(), 'style': SEED['style']}

    @app.get('/media/{asset_id}/{mode}')
    def media(asset_id: str, mode: Literal['original', 'thumb', 'download']):
        item = store.asset(asset_id)
        if not item:
            raise HTTPException(404, '리소스를 찾을 수 없습니다.')
        path = store.root / 'assets' / item['file']
        if mode == 'thumb':
            path = store.root / 'thumbs' / (asset_id + '.jpg')
        if not path.is_file():
            raise HTTPException(404, '파일을 찾을 수 없습니다.')
        return FileResponse(path, filename=item['file'] if mode == 'download' else None)

    @app.put('/api/assets/{asset_id}')
    def review(asset_id: str, req: AssetReview):
        try:
            return store.update_asset(asset_id, req.revision, req.model_dump(exclude={'revision'}))
        except KeyError:
            raise HTTPException(404, '리소스를 찾을 수 없습니다.')
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.put('/api/characters/{char_id}')
    def profile(char_id: str, req: Profile):
        if char_id not in CHAR_IDS:
            raise HTTPException(404)
        if req.master_id:
            item = store.asset(req.master_id)
            if not item or item.get('character_id') != char_id or item['media'] != 'image':
                raise HTTPException(422, '이 캐릭터의 이미지로 기준을 지정해주세요.')
        store.save_profile(char_id, req.model_dump())
        return req.model_dump()

    @app.post('/api/assets/upload')
    async def upload(file: UploadFile = File(...), title: str = Form(...), character_id: str = Form(''), kind: str = Form('other'), parent_id: str = Form('')):
        if character_id and character_id not in CHAR_IDS:
            raise HTTPException(422, '캐릭터를 확인해주세요.')
        if not title.strip() or len(title) > 160 or kind not in ('angle', 'expression', 'scene', 'other', 'audio', 'video'):
            raise HTTPException(422, '제목 또는 분류를 확인해주세요.')
        parent = store.asset(parent_id) if parent_id else None
        if parent_id and (not parent or parent.get('character_id', '') != character_id):
            raise HTTPException(422, '원본 리소스와 캐릭터가 일치해야 합니다.')
        suffix = Path(file.filename or '').suffix.lower()
        if suffix not in ('.png', '.jpg', '.jpeg', '.webp', '.mp3', '.wav', '.mp4'):
            raise HTTPException(422, 'PNG/JPG/WebP/MP3/WAV/MP4 파일을 올려주세요.')
        key = 'upload-' + uuid.uuid4().hex
        path = store.root / 'assets' / (key + suffix)
        try:
            total = 0
            with path.open('xb') as out:
                while chunk := await file.read(1024 * 1024):
                    total += len(chunk)
                    if total > 250 * 1024 * 1024:
                        raise HTTPException(413, '파일은 250MB 이하로 올려주세요.')
                    out.write(chunk)
            if suffix in ('.png', '.jpg', '.jpeg', '.webp'):
                with Image.open(path) as im:
                    im.verify()
                with Image.open(path) as im:
                    if im.width * im.height > 50000000:
                        raise ValueError('이미지 크기가 너무 큽니다.')
            else:
                result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'json', str(path)], capture_output=True, timeout=20)
                streams = json.loads(result.stdout).get('streams', []) if result.returncode == 0 else []
                expected = 'video' if suffix == '.mp4' else 'audio'
                if not any(s.get('codec_type') == expected for s in streams):
                    raise ValueError('미디어를 읽을 수 없습니다.')
            return store.add_asset(dict(id=key, file=key+suffix, title=title.strip(), character_id=character_id,
                kind=kind, version=(parent.get('version', 1)+1) if parent else 1, parent_id=parent_id,
                prompt='', reference=parent_id, tool='사용자 업로드', status='review'))
        except Exception as error:
            path.unlink(missing_ok=True)
            if isinstance(error, HTTPException):
                raise
            raise HTTPException(422, '파일 형식 또는 미디어 내용을 확인해주세요.')
        finally:
            await file.close()

    @app.post('/api/scripts/{script_id}')
    def save_script(script_id: str, req: Script):
        if not re.fullmatch('[a-z0-9-]{1,80}', script_id):
            raise HTTPException(422, '대본 ID 형식을 확인해주세요.')
        for scene in req.scenes:
            for asset_id in scene.asset_ids:
                if not store.asset(asset_id):
                    raise HTTPException(422, '연결 리소스를 찾을 수 없습니다.')
        try:
            return store.save_script(script_id, req.expected_version, req.model_dump(exclude={'expected_version'}))
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.get('/api/scripts/{script_id}/{version}/export')
    def export(script_id: str, version: int):
        item = next((s for s in store.scripts() if s['id'] == script_id and s['version'] == version), None)
        if not item:
            raise HTTPException(404)
        lines = [f"# {item['title']}", f"버전 {version} · 상태 {item['status']}", item['summary'], item['note']]
        for scene in item['scenes']:
            lines.extend([f"\n## {scene['start']}–{scene['end']}초 · {scene['title']}", scene['narration'], '\n화면: '+scene['visual'], '\n출처: '+scene['source'], '\n리소스: '+', '.join(scene['asset_ids'])])
        return Response('\n\n'.join(lines), media_type='text/markdown; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{script_id}-v{version}.md"'})

    @app.get('/scripts/{script_id}/{version}', response_class=HTMLResponse)
    def read_script(request: Request, script_id: str, version: int):
        item = next((s for s in store.scripts() if s['id'] == script_id and s['version'] == version), None)
        if not item:
            raise HTTPException(404, '대본 버전을 찾을 수 없습니다.')
        prefix = request.state.prefix
        e = escape
        clock = lambda t: f'{t // 60:02d}:{t % 60:02d}'
        versions = sorted((s for s in store.scripts() if s['id'] == script_id), key=lambda s: s['version'], reverse=True)
        version_links = ' · '.join(f'<a href="{prefix}/scripts/{e(script_id)}/{s["version"]}">v{s["version"]}</a>' for s in versions)
        rows = ''.join(f'<tr><td>{clock(s["start"])}–{clock(s["end"])}</td><td><a href="#scene-{i}">{e(s["title"])}</a></td></tr>' for i,s in enumerate(item['scenes'],1))
        sections = []
        for i,s in enumerate(item['scenes'],1):
            narration = ''.join(f'<p>{e(p)}</p>' for p in s['narration'].split('\n\n') if p.strip())
            sections.append(f'<section id="scene-{i}"><p class="time">{clock(s["start"])}–{clock(s["end"])}</p><h2>{e(s["title"])}</h2><div class="narration">{narration or "<p>내레이션 작성 전</p>"}</div><details><summary>화면 연출 · 출처 · 연결 리소스</summary><h3>화면 연출</h3><p class="preserve">{e(s["visual"])}</p><h3>사실 확인 · 출처</h3><p class="preserve">{e(s["source"])}</p><p>리소스: {e(", ".join(s["asset_ids"]))}</p></details></section>')
        status = {'outline':'구성 초안','draft':'상세 대본 초안','review':'검토 중','approved':'승인'}.get(item['status'],item['status'])
        return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(item['title'])} · v{version} · GumaStory</title><link rel="stylesheet" href="{prefix}/static/reader.css"></head><body><main><nav><a href="{prefix}/">GumaStory</a><a href="{prefix}/?script={e(script_id)}&version={version}">이 버전 편집</a><a href="{prefix}/api/scripts/{e(script_id)}/{version}/export">대본 다운로드</a></nav><header><p class="time">SCRIPT · v{version} · {status}</p><h1>{e(item['title'])}</h1><p>{e(item['summary'])}</p><p class="note">{e(item['note'])}</p><p>버전 기록: {version_links}</p></header><h2>시간대별 구성</h2><p class="note">시간은 편집 목표입니다. 실제 길이는 TTS 낭독 후 확정합니다. 화면 연출과 출처는 낭독하지 않습니다.</p><table><thead><tr><th>목표 시간</th><th>내용</th></tr></thead><tbody>{rows}</tbody></table>{''.join(sections)}<footer>GumaStory · v{version} 보존본 · 수정은 새 버전으로 저장됩니다.</footer></main></body></html>'''

    return app


app = create_app()
