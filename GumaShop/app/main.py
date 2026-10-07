import hashlib
import json
import os
import re
import subprocess
import uuid
import threading
from pathlib import Path
from urllib.parse import urlparse, quote

import httpx
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

from app.store import Store, seed, now
from app.render import render_preview

BASE = Path(__file__).parent
CATEGORIES = {'food': '푸드', 'living': '리빙', 'tech': '테크', 'beauty': '뷰티'}
Category = Literal['food', 'living', 'tech', 'beauty']


def valid_url(value):
    if not value:
        return ''
    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('HTTP 또는 HTTPS 링크를 입력해주세요.')
    return value


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Character(Model):
    revision: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=1, max_length=160)
    personality: str = Field(default='', max_length=3000)
    appearance: str = Field(default='', max_length=3000)
    room: str = Field(default='', max_length=120)
    voice: str = Field(default='', max_length=300)
    rules: str = Field(default='', max_length=3000)
    reference_id: str = ''


class Product(Model):
    revision: int | None = None
    title: str = Field(min_length=1, max_length=160)
    category: Category
    url: str = Field(default='', max_length=2000)
    features: str = Field(default='', max_length=5000)
    cautions: str = Field(default='', max_length=3000)
    source: str = Field(default='', max_length=2000)
    archived: bool = False
    _url = field_validator('url', 'source')(valid_url)


class Cut(Model):
    title: str = Field(min_length=1, max_length=100)
    seconds: int = Field(default=6, ge=1, le=60)
    visual: str = Field(default='', max_length=3000)
    narration: str = Field(default='', max_length=1500)
    prompt: str = Field(default='', max_length=5000)
    asset_id: str = ''
    method: Literal['ai', 'real', 'reuse'] = 'ai'


class Project(Model):
    revision: int | None = None
    title: str = Field(min_length=1, max_length=160)
    category: Category
    product_id: str = ''
    character_ids: list[str] = Field(min_length=1, max_length=4)
    concept: str = Field(default='', max_length=4000)
    budget: int = Field(default=0, ge=0, le=100000000)
    attempt_limit: int = Field(default=3, ge=1, le=50)
    cuts: list[Cut] = Field(default_factory=list, max_length=20)
    archived: bool = False


class Approval(Model):
    revision: int = Field(ge=1)


class Review(Approval):
    decision: Literal['approved', 'changes']
    character_ok: bool = False
    product_ok: bool = False
    claims_ok: bool = False
    note: str = Field(default='', max_length=4000)


class Feedback(Model):
    cut: int = Field(ge=0, le=20)
    text: str = Field(min_length=1, max_length=4000)


class Cost(Model):
    project_id: str
    label: str = Field(min_length=1, max_length=160)
    amount: int = Field(ge=0, le=100000000)
    attempts: int = Field(default=1, ge=1, le=1000)
    cut: int = Field(default=0, ge=0, le=20)
    note: str = Field(default='', max_length=2000)


def create_app(storage=None, dev=None, legacy=None):
    app = FastAPI(title='GumaShop Studio', docs_url=None, redoc_url=None, openapi_url=None)
    store = Store(storage or os.getenv('GUMASHOP_STORAGE', 'storage'))
    seed(store)
    app.state.store = store
    render_lock = threading.Lock()
    for job in store.all('jobs'):
        if job['status'] in ('queued', 'running'):
            store.save('jobs', dict(job, status='failed', message='서버 재시작으로 제작이 중단됐어요. 다시 제작해주세요.'), job['id'], job['revision'])
    development = (os.getenv('GUMASHOP_DEV') == '1') if dev is None else dev
    legacy_root = Path(legacy or os.getenv('GUMASHOP_LEGACY', '../GumaVideoFactory/storage'))
    templates = Jinja2Templates(directory=BASE / 'templates')

    @app.middleware('http')
    async def protection(request: Request, call_next):
        path = request.url.path
        prefix = '/gumashop' if request.headers.get('x-forwarded-prefix') == '/gumashop' else ''
        request.state.prefix = prefix
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            if request.headers.get('x-gumashop') != 'studio' or (origin and urlparse(origin).netloc != request.headers.get('host')):
                return JSONResponse({'detail': '이 작업실에서 다시 요청해주세요.'}, 403)
        if path != '/health' and not development:
            cookie = request.cookies.get('guma_sso_token')
            allowed = False
            if cookie:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        result = await client.get(os.getenv('GUMASHOP_AUTH_URL', 'http://host.docker.internal:8081/auth'),
                                                  cookies={'guma_sso_token': cookie})
                        allowed = result.status_code == 200
                except httpx.HTTPError:
                    pass
            if not allowed:
                if path.startswith('/api/'):
                    return JSONResponse({'detail': '홈서버 로그인이 필요합니다. 페이지를 새로고침해주세요.'}, 401)
                target = 'https://home.guma3d.com/gumashop/' if prefix else 'https://gumashop.guma3d.com/'
                return RedirectResponse('https://home.guma3d.com/login?redirect_url=' + quote(target, safe=''), 302)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        if path.startswith('/api/') or path == '/':
            response.headers['Cache-Control'] = 'no-store'
        return response

    app.mount('/static', StaticFiles(directory=BASE / 'static'), name='static')

    @app.get('/health')
    def health():
        with store.connect() as db:
            db.execute('SELECT 1')
        return {'status': 'ok'}

    @app.get('/')
    def index(request: Request):
        return templates.TemplateResponse(request=request, name='index.html', context={'prefix': request.state.prefix})

    @app.get('/api/state')
    def state():
        return {**{key: store.all(key) for key in ('products', 'projects', 'assets', 'videos', 'costs', 'feedback', 'jobs')},
                'characters': [store.get('characters', key) for key in ('tiger', 'rabbit', 'pig', 'cat')],
                'asset_audit': next(iter(store.all('asset_audits')), None),
                'categories': CATEGORIES, 'legacy_available': (legacy_root / 'products').is_dir(),
                'generation_connected': False, 'publishing_connected': False}

    @app.put('/api/characters/{key}')
    def character(key: str, req: Character):
        old = store.get('characters', key)
        if req.reference_id:
            asset = store.get('assets', req.reference_id)
            if asset['kind'] != 'image' or asset.get('archived'):
                raise HTTPException(400, '사용 가능한 이미지 자산을 선택해주세요.')
        return store.save('characters', {**old, **req.model_dump(exclude={'revision'})}, key, req.revision)

    @app.post('/api/products')
    def create_product(req: Product):
        return store.save('products', req.model_dump(exclude={'revision'}))

    @app.put('/api/products/{key}')
    def update_product(key: str, req: Product):
        old = store.get('products', key)
        return store.save('products', {**old, **req.model_dump(exclude={'revision'})}, key, req.revision)

    def validate_project(req):
        if len(set(req.character_ids)) != len(req.character_ids):
            raise HTTPException(400, '출연 캐릭터가 중복되었습니다.')
        for key in req.character_ids:
            store.get('characters', key)
        if req.product_id:
            product = store.get('products', req.product_id)
            if product['archived']:
                raise HTTPException(400, '보관된 상품입니다. 먼저 복원해주세요.')
        for cut in req.cuts:
            if cut.asset_id:
                asset = store.get('assets', cut.asset_id)
                if asset.get('archived'):
                    raise HTTPException(400, '보관된 자산이 콘티에 포함되어 있습니다.')

    @app.post('/api/projects')
    def create_project(req: Project):
        validate_project(req)
        return store.save('projects', dict(req.model_dump(exclude={'revision'}), approved_at=None, approved_revision=None))

    @app.put('/api/projects/{key}')
    def update_project(key: str, req: Project):
        old = store.get('projects', key)
        validate_project(req)
        return store.save('projects', {**old, **req.model_dump(exclude={'revision'}), 'approved_at': None,
                                      'approved_revision': None}, key, req.revision)

    @app.get('/api/projects/{key}/history')
    def history(key: str):
        return store.history('projects', key)

    @app.post('/api/projects/{key}/approve')
    def approve(key: str, req: Approval):
        project = store.get('projects', key)
        if project.get('archived') or not project['cuts'] or not all(c['visual'] for c in project['cuts']):
            raise HTTPException(400, '모든 컷의 화면 설명을 입력하고 보관 상태를 해제해주세요.')
        if not project['product_id']:
            raise HTTPException(400, '소개할 상품을 먼저 연결해주세요.')
        product = store.get('products', project['product_id'])
        if product['archived']:
            raise HTTPException(400, '보관된 상품을 먼저 복원해주세요.')
        return store.save('projects', dict(project, approved_at=now(), approved_revision=req.revision + 1,
                                          production_references={'product': product, 'characters': [
                                              store.get('characters', k) for k in project['character_ids']]}), key, req.revision)

    @app.get('/api/projects/{key}/export')
    def export(key: str):
        project = store.get('projects', key)
        asset_ids = {cut['asset_id'] for cut in project['cuts'] if cut['asset_id']}
        characters = [store.get('characters', item) for item in project['character_ids']]
        asset_ids.update(c['reference_id'] for c in characters if c['reference_id'])
        payload = {'schema': 'gumashop.production.v1', 'exported_at': now(), 'project': project,
                   'product': store.get('products', project['product_id']) if project['product_id'] else None,
                   'characters': characters, 'assets': [store.get('assets', k) for k in sorted(asset_ids)],
                   'history': store.history('projects', key),
                   **{k: [i for i in store.all(k) if i['project_id'] == key] for k in ('videos', 'costs', 'feedback')},
                   'note': '미디어는 포함되지 않습니다. 각 자산은 작업실에서 별도로 다운로드하세요.'}
        return JSONResponse(payload, headers={'Content-Disposition': f'attachment; filename="gumashop-{key}.json"'})

    async def save_media(file, video_only=False):
        extension = Path(file.filename or '').suffix.lower()
        allowed = {'.mp4', '.webm', '.mov'} if video_only else {'.png', '.jpg', '.jpeg', '.webp', '.mp4', '.webm', '.mov'}
        if extension not in allowed:
            raise HTTPException(400, 'PNG, JPG, WebP 또는 MP4, WebM, MOV 파일을 선택해주세요.')
        name = uuid.uuid4().hex + extension
        path = store.root / 'media' / name
        size, sha = 0, hashlib.sha256()
        try:
            with path.open('wb') as output:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > 150 * 1024 * 1024:
                        raise HTTPException(413, '파일은 150MB 이하로 등록해주세요.')
                    output.write(chunk)
                    sha.update(chunk)
            kind = 'video' if extension in {'.mp4', '.webm', '.mov'} else 'image'
            duration = None
            if kind == 'image':
                with Image.open(path) as picture:
                    if picture.format not in {'PNG', 'JPEG', 'WEBP'} or picture.width * picture.height > 30000000:
                        raise ValueError('image')
                    picture.verify()
            else:
                result = subprocess.run(['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe',
                                         '-f', 'matroska' if extension == '.webm' else 'mov',
                                         '-show_entries', 'format=duration:stream=codec_type',
                                         '-of', 'json', str(path)], capture_output=True, timeout=20)
                info = json.loads(result.stdout)
                duration = float(info.get('format', {}).get('duration', 0))
                if result.returncode or duration <= 0 or not any(s.get('codec_type') == 'video' for s in info.get('streams', [])):
                    raise ValueError('video')
            return dict(filename=name, original_name=Path(file.filename).name[:200], kind=kind,
                        bytes=size, sha256=sha.hexdigest(), duration=duration)
        except HTTPException:
            path.unlink(missing_ok=True)
            raise
        except (ValueError, OSError, UnidentifiedImageError, subprocess.TimeoutExpired, Image.DecompressionBombError):
            path.unlink(missing_ok=True)
            raise HTTPException(400, '파일을 읽을 수 없습니다. 정상 이미지 또는 영상인지 확인해주세요.')
        finally:
            await file.close()

    @app.post('/api/assets')
    async def upload_asset(file: UploadFile = File(...), title: str = Form(...), character_id: str = Form(''),
                           space: str = Form(''), action: str = Form(''), source: str = Form('')):
        if not title.strip() or len(title) > 160 or max(len(space), len(action), len(source)) > 2000:
            raise HTTPException(400, '자산 이름과 설명 길이를 확인해주세요.')
        if character_id:
            store.get('characters', character_id)
        try:
            valid_url(source)
        except ValueError as error:
            raise HTTPException(400, str(error))
        media = await save_media(file)
        try:
            return store.save('assets', dict(media, title=title.strip(), character_id=character_id, space=space,
                                            action=action, source=source, archived=False))
        except Exception:
            (store.root / 'media' / media['filename']).unlink(missing_ok=True)
            raise

    @app.post('/api/assets/{key}/archive')
    def archive_asset(key: str, req: Approval):
        asset = store.get('assets', key)
        if not asset['archived']:
            used = any(c['reference_id'] == key for c in store.all('characters')) or any(
                cut['asset_id'] == key for p in store.all('projects') if not p['archived'] for cut in p['cuts'])
            if used:
                raise HTTPException(409, '캐릭터 또는 콘티에서 사용 중입니다. 연결을 해제한 후 보관해주세요.')
        return store.save('assets', dict(asset, archived=not asset['archived']), key, req.revision)

    @app.get('/api/{kind}/{key}/file')
    def media_file(kind: Literal['assets', 'videos'], key: str, download: bool = False):
        item = store.get(kind, key)
        path = store.root / 'media' / item['filename']
        if not path.is_file():
            raise HTTPException(404, '미디어 파일을 찾을 수 없습니다.')
        return FileResponse(path, filename=item['original_name'] if download else None)

    @app.post('/api/projects/{key}/videos')
    async def upload_video(key: str, revision: int = Form(...), note: str = Form(''), file: UploadFile = File(...)):
        project = store.get('projects', key)
        if project['revision'] != revision or not project['approved_at'] or project['archived']:
            raise HTTPException(409, '현재 콘티를 먼저 제작 승인해주세요.')
        if len(note) > 4000:
            raise HTTPException(400, '메모는 4,000자 이하로 입력해주세요.')
        media = await save_media(file, video_only=True)
        latest = store.get('projects', key)
        if latest['revision'] != revision:
            (store.root / 'media' / media['filename']).unlink(missing_ok=True)
            raise HTTPException(409, '업로드 중 콘티가 바뀌었습니다. 새 콘티를 확인해주세요.')
        try:
            return store.save('videos', dict(media, project_id=key, storyboard_revision=revision, storyboard=project,
                                            note=note, status='review', review=None))
        except Exception:
            (store.root / 'media' / media['filename']).unlink(missing_ok=True)
            raise

    @app.post('/api/projects/{key}/render')
    def start_render(key: str, req: Approval, tasks: BackgroundTasks):
        project = store.get('projects', key)
        if project['revision'] != req.revision or not project['approved_at'] or project['archived']:
            raise HTTPException(409, '현재 콘티를 먼저 제작 승인해주세요.')
        if not project['cuts'] or sum(c['seconds'] for c in project['cuts']) > 180:
            raise HTTPException(400, '프리뷰는 1컷 이상, 전체 180초 이내로 만들어주세요.')
        for cut in project['cuts']:
            if not cut['asset_id']:
                raise HTTPException(400, '모든 컷에 이미지나 영상 자산을 연결해주세요.')
            asset = store.get('assets', cut['asset_id'])
            if asset['archived'] or not (store.root / 'media' / asset['filename']).is_file():
                raise HTTPException(400, '사용할 수 없는 자산이 있어요. 컷별 자산을 확인해주세요.')
        if not render_lock.acquire(blocking=False):
            raise HTTPException(409, '다른 프리뷰를 제작 중이에요. 완료 후 다시 시도해주세요.')
        try:
            job = store.save('jobs', dict(project_id=key, storyboard_revision=req.revision, status='queued',
                                         message='콘티 프리뷰 제작을 준비하고 있어요.'))
            tasks.add_task(render_preview, store, job['id'], project, render_lock.release)
            return job
        except Exception:
            render_lock.release()
            raise

    @app.post('/api/videos/{key}/review')
    def review_video(key: str, req: Review):
        video = store.get('videos', key)
        if video['status'] != 'review':
            raise HTTPException(409, '검수가 완료된 버전입니다. 수정본을 새 버전으로 등록해주세요.')
        if req.decision == 'approved' and not (req.character_ok and req.product_ok and req.claims_ok):
            raise HTTPException(400, '캐릭터·상품·표현을 모두 확인해주세요.')
        if req.decision == 'changes' and not req.note:
            raise HTTPException(400, '수정할 내용을 입력해주세요.')
        project = store.get('projects', video['project_id'])
        if req.decision == 'approved' and (project['archived'] or project['revision'] != video['storyboard_revision']):
            raise HTTPException(409, '현재 콘티와 다른 버전입니다. 현재 승인 콘티의 영상을 등록해주세요.')
        return store.save('videos', dict(video, status=req.decision, review=dict(req.model_dump(), reviewed_at=now())), key, req.revision)

    @app.post('/api/videos/{key}/feedback')
    def feedback(key: str, req: Feedback):
        video = store.get('videos', key)
        if req.cut > len(video['storyboard']['cuts']):
            raise HTTPException(400, '해당 영상 콘티의 컷 번호를 선택해주세요.')
        return store.save('feedback', dict(req.model_dump(), video_id=key, project_id=video['project_id']))

    @app.post('/api/costs')
    def cost(req: Cost):
        project = store.get('projects', req.project_id)
        if req.cut > len(project['cuts']):
            raise HTTPException(400, '존재하는 컷 번호를 선택해주세요.')
        return store.save('costs', dict(req.model_dump(), voided=False))

    @app.post('/api/costs/{key}/void')
    def void_cost(key: str, req: Approval):
        cost = store.get('costs', key)
        return store.save('costs', dict(cost, voided=not cost['voided']), key, req.revision)

    def legacy_items():
        result = []
        for path in sorted((legacy_root / 'products').glob('*/idea.json')):
            if not re.fullmatch(r'[a-f0-9]{16}', path.parent.name):
                continue
            try:
                item = json.loads(path.read_text(encoding='utf-8'))
                rec = item.get('recommendation', {})
                if item.get('archived'):
                    continue
                category = {'household': 'living'}.get(item.get('category'), item.get('category'))
                if category not in CATEGORIES:
                    continue
                link = rec.get('purchase_link') or {}
                url = link.get('url', '') if isinstance(link, dict) else ''
                try:
                    valid_url(url)
                except ValueError:
                    url = ''
                result.append(dict(id=path.parent.name, title=str(item.get('title') or rec.get('subject') or '이전 제작')[:160],
                                   category=category, url=url, features=str(rec.get('key_feature') or rec.get('hook') or '')[:5000],
                                   cautions=str(rec.get('cautions') or '')[:3000],
                                   videos=len(list((path.parent / 'Video').glob('v*/version.json'))),
                                   source_url='https://videofactory.guma3d.com/ideas/' + path.parent.name))
            except (OSError, ValueError, AttributeError, TypeError):
                continue
        return result

    @app.get('/api/legacy')
    def legacy_list():
        return {'available': (legacy_root / 'products').is_dir(), 'items': legacy_items()}

    @app.post('/api/legacy/{key}/import')
    def import_legacy(key: str):
        item = next((i for i in legacy_items() if i['id'] == key), None)
        if not item:
            raise HTTPException(404, '기존 제작 항목을 찾을 수 없습니다.')
        identity = 'legacy-' + key
        # Stable identity makes repeated imports idempotent without changing local edits.
        try:
            return store.get('products', identity)
        except HTTPException as error:
            if error.status_code != 404:
                raise
        return store.save('products', dict(title=item['title'], category=item['category'], url=item['url'],
                                           features=item['features'], cautions=item['cautions'], source=item['source_url'],
                                           legacy_id=key, archived=False), identity)

    return app


app = create_app()
