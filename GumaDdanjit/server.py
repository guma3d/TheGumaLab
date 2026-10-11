"""One authenticated process, three production modules, one cross-format library."""
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

PREFIX = '/gumaddanjit'
BASE = Path(__file__).parent
DATA = Path(os.getenv('DDANJIT_DATA', '/data'))
os.environ.setdefault('GUMADDANJIT_SHORTS_STORAGE', str(DATA/'shorts'))
os.environ.setdefault('GUMASTORY_STORAGE', str(DATA/'story'))
os.environ.setdefault('GUMASHOP_STORAGE', str(DATA/'shop'))
os.environ.setdefault('GUMASHOP_LEGACY', str(DATA/'shorts'))
from app.main import app as shorts
from app.core import versions
from story.main import app as story
from shop.main import app as shop

NAV = '''<link rel="stylesheet" href="/gumaddanjit/static/shell.css"><nav class="dd-nav" aria-label="통합 제작실"><a href="/gumaddanjit/">GumaDdanjit</a><a href="/gumaddanjit/shorts/">쇼츠</a><a href="/gumaddanjit/story/">출퇴근 이야기</a><a href="/gumaddanjit/shop/">프리미엄 쇼핑</a><a href="/gumaddanjit/#library">전체 보관함</a><a href="/gumatts/">음성 작업실</a></nav>'''

def scoped_text(text, prefix):
    # Old shorts records retain their exact contents; qualify URLs only at the HTTP boundary.
    return re.sub(r'''(["'`])/(?!/|gumaddanjit(?:/|["'`])|gumatts/)(?=(?:api|storage|ideas|legacy|static|products)(?:/|[?"'`])|[?"'`])''', lambda m:m[1]+prefix+'/', text)

class Module:
    def __init__(self, child, section):
        self.child, self.section = child, section

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http': return await self.child(scope, receive, send)
        local = dict(scope)
        mount = scope.get('root_path', '')
        path = scope['path']
        if mount and path.startswith(mount): path = path[len(mount):] or '/'
        local.update(path=path, raw_path=path.encode(), root_path='')
        prefix = PREFIX+'/'+self.section
        start = None
        chunks = []
        rewrite = False
        async def output(message):
            nonlocal start, rewrite
            if message['type']=='http.response.start':
                start = dict(message)
                headers = dict(message['headers'])
                content_type = headers.get(b'content-type', b'').decode()
                rewrite = any(t in content_type for t in ('text/html', 'application/json', 'javascript'))
                if b'location' in headers and headers[b'location'].startswith(b'/') and not headers[b'location'].startswith(PREFIX.encode()):
                    headers[b'location'] = prefix.encode()+headers[b'location']
                start['headers'] = list(headers.items())
                if not rewrite: await send(start)
            elif message['type']=='http.response.body' and rewrite:
                chunks.append(message.get('body', b''))
                if message.get('more_body'): return
                text = b''.join(chunks).decode('utf-8')
                if self.section=='shorts': text = scoped_text(text, prefix)
                headers = dict(start['headers'])
                if b'text/html' in headers.get(b'content-type',b'') and path!='/products':
                    text = re.sub(r'(<body\b[^>]*>)', lambda m:m[1]+NAV, text, count=1, flags=re.I)
                body = text.encode()
                headers[b'content-length'] = str(len(body)).encode()
                headers.pop(b'etag',None)
                start['headers'] = list(headers.items())
                await send(start)
                await send({'type':'http.response.body','body':body})
            else: await send(message)
        await self.child(local, receive, output)

@asynccontextmanager
async def lifespan(app):
    if os.getenv('DDANJIT_WORKER','0')=='1':
        async with shorts.router.lifespan_context(shorts): yield
    else: yield

app = FastAPI(title='GumaDdanjit', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

@app.middleware('http')
async def protect(request: Request, call_next):
    path = request.url.path
    public = path=='/health' or (path=='/shorts/products' and request.method in ('GET','HEAD'))
    if not public:
        allowed = False
        cookie = request.cookies.get('guma_sso_token')
        if cookie:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    r=await client.get(os.getenv('DDANJIT_AUTH_URL','http://host.docker.internal:8081/auth'),cookies={'guma_sso_token':cookie})
                    allowed = r.status_code==200
            except httpx.HTTPError: pass
        if not allowed:
            if '/api/' in path or '/media/' in path or '/storage/' in path:
                return JSONResponse({'detail':'홈서버 로그인이 필요합니다.'},401)
            target='https://home.guma3d.com'+PREFIX+path+('?' + request.url.query if request.url.query else '')
            return RedirectResponse('https://home.guma3d.com/login?redirect_url='+quote(target,safe=''),302)
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=urlparse(request.headers.get('origin',''))
            if origin.scheme not in ('http','https') or origin.netloc!=request.headers.get('host'):
                return JSONResponse({'detail':'같은 제작실에서 다시 요청해주세요.'},403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Cache-Control']='private, no-store'
    return response

@app.get('/health')
def health():
    with story.state.store.connect() as db: db.execute('SELECT 1')
    with shop.state.store.connect() as db: db.execute('SELECT 1')
    if not versions.ROOT.is_dir(): return JSONResponse({'status':'missing-storage'},503)
    return {'status':'ok','service':'GumaDdanjit','modules':['shorts','story','shop']}

@app.get('/')
def index(): return HTMLResponse((BASE/'static/index.html').read_text(encoding='utf-8'))

@app.get('/api/library')
def library():
    projects=[];assets=[]
    for file in sorted(versions.ROOT.glob('*/idea.json')):
        item=json.loads(file.read_text(encoding='utf-8'))
        if item.get('archived'): continue
        history=versions.history(item['id'],'Video')
        latest=history[0] if history else {}
        projects.append(dict(id='shorts:'+item['id'],section='shorts',title=item['title'],status=latest.get('status','기획'),versions=len(history),url=PREFIX+'/shorts/ideas/'+item['id']))
        for v in history:
            folder=versions.version_dir(item['id'],'Video',v['number'])
            file=folder/'final.mp4'
            if file.exists():
                assets.append(dict(id='shorts:'+item['id']+':'+str(v['number']),section='shorts',title=item['title']+' · v'+str(v['number']),kind='video',status=v.get('status','review'),url=PREFIX+'/shorts/ideas/'+item['id']+'?video='+str(v['number'])+'#Video',media_url=PREFIX+'/shorts'+versions.url(file)))
    scripts={}
    for item in story.state.store.scripts():
        previous=scripts.get(item['id'])
        if not previous or item['version']>previous['version']: scripts[item['id']]=item
    for item in scripts.values():
        projects.append(dict(id='story:'+item['id'],section='story',title=item['title'],status=item['status'],versions=item['version'],url=PREFIX+'/story/?script='+item['id']+'&version='+str(item['version'])))
    for item in story.state.store.assets():
        if item.get('archived'):continue
        if item['media'] in ('video','audio'):
            assets.append(dict(id='story:'+item['id'],section='story',title=item['title'],kind=item['media'],status=item['status'],url=PREFIX+'/story/watch/'+item['id'] if item['media']=='video' else PREFIX+'/story/',media_url=PREFIX+'/story/media/'+item['id']+'/original'))
    products={i['id']:i for i in shop.state.store.all('projects')}
    for item in products.values():
        if item.get('archived'):continue
        projects.append(dict(id='shop:'+item['id'],section='shop',title=item['title'],status='승인' if item.get('approved_at') else '기획',versions=item['revision'],url=PREFIX+'/shop/#project/'+item['id']))
    for item in shop.state.store.all('videos'):
        title=products.get(item['project_id'],{}).get('title','쇼핑 영상')
        assets.append(dict(id='shop:'+item['id'],section='shop',title=title+' · '+item.get('original_name',item['id']),kind='video',status=item['status'],url=PREFIX+'/shop/#project/'+item['project_id']+'/videos',media_url=PREFIX+'/shop/api/videos/'+item['id']+'/file'))
    return {'projects':projects,'assets':assets,'voice_policy':{'shorts':'F4','story':'M5','shop':'F4'}}

app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
app.mount('/shorts',Module(shorts,'shorts'))
app.mount('/story',Module(story,'story'))
app.mount('/shop',Module(shop,'shop'))
