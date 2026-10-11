import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT=Path(tempfile.mkdtemp(prefix='ddanjit-test-'))
os.environ['DDANJIT_DATA']=str(ROOT)
os.environ['GUMADDANJIT_SHORTS_STORAGE']=str(ROOT/'shorts')
os.environ['GUMASTORY_STORAGE']=str(ROOT/'story')
os.environ['GUMASHOP_STORAGE']=str(ROOT/'shop')
os.environ['DDANJIT_WORKER']='0'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
import pytest
from fastapi.testclient import TestClient
import server

@pytest.fixture
def client():
    server.versions.ROOT.mkdir(parents=True,exist_ok=True)
    with TestClient(server.app) as c:
        c.cookies.set('guma_sso_token','test-session')
        c.headers['Origin']='http://testserver'
        with patch('httpx.AsyncClient.get',return_value=httpx.Response(200)):yield c

def test_private_routes_and_public_catalog():
    with TestClient(server.app) as c:
        for path in ['/api/library','/shorts/api/ideas/x','/story/api/state','/shop/api/state','/shorts/storage/private.json']:
            assert c.get(path,follow_redirects=False).status_code==401
        assert c.get('/story/',follow_redirects=False).status_code==302
        assert c.get('/shorts/products').status_code==200
        assert c.post('/shorts/products',follow_redirects=False).status_code!=200

def test_pages_routes_and_unified_library(client):
    for section in ['shorts','story','shop']:
        r=client.get('/'+section+'/')
        assert r.status_code==200,r.text[:200]
        assert '통합 제작실' in r.text and '/gumaddanjit/static/archive.css' in r.text
        assert '리소스' in r.text and '이미지 콘셉트' in r.text and '완성 영상' in r.text
        assert '<textarea' not in r.text
    assert client.get('/story/api/state').status_code==200
    assert client.get('/shop/api/state').status_code==200
    idea=server.versions.create({'category':'food','subject':'통합 회귀 테스트'},'2026-10-11')
    assert client.get('/shorts/ideas/'+idea['id']).status_code==200
    html=client.get('/shorts/').text
    assert 'href="/?category=' not in html
    assert '/gumaddanjit/shorts/' in html
    library=client.get('/api/library').json()
    assert any(x['id']=='shorts:'+idea['id'] for x in library['projects'])
    assert any(x['section']=='story' for x in library['projects'])


def test_archive_preserves_versions_and_removes_web_feedback(client):
    idea = server.versions.create({'category': 'food', 'subject': '버전 보존'}, '2026-10-12')
    for number in (1, 2):
        folder = server.versions.version_dir(idea['id'], 'Video', number)
        folder.mkdir(parents=True, exist_ok=True)
        server.versions.write_json(folder/'version.json', {
            'number': number, 'status': 'complete',
            'output_url': f'/storage/products/{idea["id"]}/Video/v{number:04d}/final.mp4'})
    data = client.get('/api/archive').json()['items']
    videos = [x for x in data if x['project'] == idea['id'] and x['group'] == 'videos']
    assert {x['version'] for x in videos} == {1, 2}
    assert all(x['media_url'].startswith('/gumaddanjit/shorts/storage/') for x in videos)
    assert all(x['group'] in ('resources', 'concepts', 'videos') for x in data)
    for child in (server.shorts, server.shop):
        assert not any('feedback' in getattr(r, 'path', '') for r in child.routes)
    for path in ['/shorts/ideas/'+idea['id'], '/story/watch/example', '/story/scripts/promotion/1']:
        assert 'archive.js' in client.get(path).text

def test_write_conflicts_and_cross_site_fail_closed(client):
    assert client.post('/shop/api/products',json={},headers={'Origin':'https://evil.example','X-GumaShop':'studio'}).status_code==403
    h={'X-GumaShop':'studio'}
    item=client.post('/shop/api/products',json={'title':'검증 상품','category':'food'},headers=h)
    assert item.status_code==200,item.text
    item=item.json()
    assert client.put('/shop/api/products/'+item['id'],json={'title':'수정','category':'food','revision':999},headers=h).status_code==409
    s=client.get('/story/api/state').json()['scripts'][0]
    body={k:s[k] for k in ['title','summary','status','note','scenes']}
    body['expected_version']=s['version']
    r=client.post('/story/api/scripts/'+s['id'],json=body,headers={'X-GumaStory':'studio'})
    assert r.status_code==200,r.text
    assert client.post('/story/api/scripts/'+s['id'],json=body,headers={'X-GumaStory':'studio'}).status_code==409

def test_scoped_urls_and_streaming_range(client):
    sample=server.DATA/'shorts/test-range.mp4';sample.write_bytes(b'0123456789'*100)
    r=client.get('/shorts/storage/test-range.mp4',headers={'Range':'bytes=10-19'})
    assert r.status_code==206 and r.content==b'0123456789'
    assert server.scoped_text('"/storage/a.mp4" "https://example.org/a"', '/gumaddanjit/shorts')=='"/gumaddanjit/shorts/storage/a.mp4" "https://example.org/a"'
    assert server.scoped_text('"/gumaddanjit/story/"','/gumaddanjit/shorts')=='"/gumaddanjit/story/"'


def test_browser_headers_remain_ascii():
    from pathlib import Path
    for section, header in [('story', 'X-GumaStory'), ('shop', 'X-GumaShop')]:
        source = (Path(__file__).parents[1]/section/'static/app.js').read_text()
        assert header in source
        assert 'X-GumaDdanjit' not in source


def test_local_storyboard_render(tmp_path):
    from PIL import Image
    from shop.store import Store
    from shop.render import render_preview
    import subprocess
    store=Store(tmp_path)
    Image.new('RGB',(180,320),'gold').save(tmp_path/'media'/'sample.png')
    asset=store.save('assets',{'filename':'sample.png','kind':'image'})
    project=store.save('projects',{'cuts':[{'asset_id':asset['id'],'seconds':0.5}]})
    job=store.save('jobs',{'status':'queued'})
    released=[]
    render_preview(store,job['id'],project,lambda:released.append(True))
    result=store.get('jobs',job['id'])
    assert result['status']=='complete'
    video=store.get('videos',result['video_id'])
    probe=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height','-of','json',str(tmp_path/'media'/video['filename'])],capture_output=True,text=True,check=True)
    assert json.loads(probe.stdout)['streams'][0]=={'width':720,'height':1280}
    assert released==[True]
