import io
import json
import re
import subprocess

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app

HEADERS = {'X-GumaShop': 'studio'}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'data', dev=True, legacy=tmp_path / 'legacy'), headers=HEADERS) as client:
        yield client


def product(client):
    response = client.post('/api/products', json={'title': '고구마빵', 'category': 'food', 'url': 'https://example.com/product'})
    assert response.status_code == 200, response.text
    return response.json()


def project(client):
    response = client.post('/api/projects', json={'title': '가족의 간식', 'category': 'food',
        'product_id': product(client)['id'], 'character_ids': ['rabbit', 'pig'], 'budget': 10000,
        'cuts': [{'title': '주방', 'visual': '엄마가 주방에서 빵을 준비한다', 'seconds': 6}]})
    assert response.status_code == 200, response.text
    return response.json()


def payload(p):
    return {k: p[k] for k in ('revision', 'title', 'category', 'product_id', 'character_ids', 'concept',
                              'budget', 'attempt_limit', 'cuts', 'archived')}


def approve(client, p):
    result = client.post(f"/api/projects/{p['id']}/approve", json={'revision': p['revision']})
    assert result.status_code == 200, result.text
    return result.json()


def test_first_run_and_restart(tmp_path):
    path = tmp_path / 'data'
    c = TestClient(create_app(path, dev=True), headers=HEADERS)
    state = c.get('/api/state').json()
    assert len(state['characters']) == 4
    assert state['projects'] == []
    p = product(c)
    c.close()
    with TestClient(create_app(path, dev=True), headers=HEADERS) as restarted:
        assert restarted.get('/api/state').json()['products'][0]['id'] == p['id']
        assert len(restarted.get('/api/state').json()['characters']) == 4


def test_versions_conflict_and_approval_reset(client):
    p = project(client)
    approved = approve(client, p)
    assert approved['production_references']['characters'][0]['name'] == '토끼 엄마'
    assert client.put('/api/projects/' + p['id'], json=payload(p)).status_code == 409
    updated = client.put('/api/projects/' + p['id'], json={**payload(approved), 'title': '새 콘티'})
    assert updated.status_code == 200
    assert updated.json()['approved_at'] is None
    history = client.get('/api/projects/' + p['id'] + '/history').json()
    assert len(history) == 3
    assert history[-1]['title'] == '가족의 간식'
    assert history[1]['approved_at']
    export = client.get('/api/projects/' + p['id'] + '/export')
    assert export.json()['schema'] == 'gumashop.production.v1'
    assert 'attachment' in export.headers['content-disposition']


def test_validation_and_csrf(client):
    assert client.post('/api/products', json={'title': ' ', 'category': 'food'}).status_code == 422
    assert client.post('/api/products', json={'title': 'x', 'category': 'food', 'url': 'javascript:alert(1)'}).status_code == 422
    assert client.post('/api/products', json={'title': 'x', 'category': 'food'}, headers={'origin': 'https://evil.test'}).status_code == 403
    assert client.post('/api/projects', json={'title': 'x', 'category': 'food', 'character_ids': ['unknown']}).status_code == 404
    p = project(client)
    changed = client.put('/api/projects/' + p['id'], json={**payload(p), 'cuts': []}).json()
    assert client.post('/api/projects/' + p['id'] + '/approve', json={'revision': changed['revision']}).status_code == 400


def test_authentication_required(tmp_path):
    with TestClient(create_app(tmp_path / 'auth', dev=False)) as c:
        assert c.get('/health').status_code == 200
        assert c.get('/api/state').status_code == 401
        assert c.get('/', follow_redirects=False).status_code == 302
        assert c.post('/api/products', json={'title': 'x', 'category': 'food'}).status_code == 403
        assert c.get('/static/app.js', follow_redirects=False).status_code == 302


def test_assets_and_media_validation(client):
    data = io.BytesIO()
    Image.new('RGB', (12, 12), 'orange').save(data, 'PNG')
    response = client.post('/api/assets', data={'title': '기준 이미지', 'character_id': 'rabbit'},
                           files={'file': ('reference.png', data.getvalue(), 'image/png')})
    assert response.status_code == 200, response.text
    asset = response.json()
    file = client.get('/api/assets/' + asset['id'] + '/file')
    assert file.content == data.getvalue()
    assert file.headers['x-content-type-options'] == 'nosniff'
    p = project(client)
    cut = {**p['cuts'][0], 'asset_id': asset['id']}
    assert client.put('/api/projects/' + p['id'], json={**payload(p), 'cuts': [cut]}).status_code == 200
    assert client.post('/api/assets/' + asset['id'] + '/archive', json={'revision': 1}).status_code == 409
    invalid = client.post('/api/assets', data={'title': 'invalid'}, files={'file': ('x.png', b'not an image', 'image/png')})
    assert invalid.status_code == 400
    assert len(list((client.app.state.store.root / 'media').iterdir())) == 1


def test_costs_are_reversible(client):
    p = project(client)
    data = {'project_id': p['id'], 'label': '영상 생성', 'amount': 3000, 'attempts': 2, 'cut': 1}
    c = client.post('/api/costs', json=data).json()
    assert c['amount'] == 3000
    void = client.post('/api/costs/' + c['id'] + '/void', json={'revision': 1}).json()
    assert void['voided']
    restored = client.post('/api/costs/' + c['id'] + '/void', json={'revision': void['revision']}).json()
    assert not restored['voided']
    assert client.post('/api/costs', json={**data, 'cut': 2}).status_code == 400


def test_read_only_idempotent_legacy_import(tmp_path):
    root = tmp_path / 'legacy'
    folder = root / 'products' / '0123456789abcdef'
    folder.mkdir(parents=True)
    content = json.dumps({'title': '이전 상품', 'category': 'household', 'recommendation': {}})
    (folder / 'idea.json').write_text(content, encoding='utf-8')
    with TestClient(create_app(tmp_path / 'data', dev=True, legacy=root), headers=HEADERS) as c:
        assert c.get('/api/legacy').json()['items'][0]['category'] == 'living'
        first = c.post('/api/legacy/0123456789abcdef/import').json()
        second = c.post('/api/legacy/0123456789abcdef/import').json()
        assert first == second
        assert (folder / 'idea.json').read_text(encoding='utf-8') == content
        assert len(c.get('/api/state').json()['products']) == 1


def test_video_review_feedback_and_stale_board(client, tmp_path):
    path = tmp_path / 'test.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=green:s=64x64:d=1',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)], check=True)
    p = project(client)
    def upload(p):
        return client.post('/api/projects/' + p['id'] + '/videos', data={'revision': p['revision']},
                            files={'file': ('test.mp4', path.read_bytes(), 'video/mp4')})
    assert upload(p).status_code == 409
    p = approve(client, p)
    response = upload(p)
    assert response.status_code == 200, response.text
    v = response.json()
    assert v['storyboard']['production_references']['product']['title'] == '고구마빵'
    review = {'revision': 1, 'decision': 'approved', 'character_ok': True, 'product_ok': True, 'claims_ok': True}
    assert client.post('/api/videos/' + v['id'] + '/review', json={**review, 'claims_ok': False}).status_code == 400
    assert client.post('/api/videos/' + v['id'] + '/feedback', json={'cut': 2, 'text': '수정'}).status_code == 400
    assert client.post('/api/videos/' + v['id'] + '/feedback', json={'cut': 1, 'text': '제품을 크게'}).status_code == 200
    reviewed = client.post('/api/videos/' + v['id'] + '/review', json=review)
    assert reviewed.json()['status'] == 'approved'
    assert client.post('/api/videos/' + v['id'] + '/review', json={**review, 'revision': 2}).status_code == 409
    second = upload(p).json()
    client.put('/api/projects/' + p['id'], json={**payload(p), 'title': '변경됨'})
    assert client.post('/api/videos/' + second['id'] + '/review', json=review).status_code == 409


def test_proxy_prefix(client):
    response = client.get('/', headers={'x-forwarded-prefix': '/gumashop'})
    assert re.search(r'<base\s+href="/gumashop/"\s*/?>', response.text)
    assert "object-src 'none'" in response.headers['content-security-policy']


def test_local_storyboard_render(client):
    p = approve(client, project(client))
    assert client.post('/api/projects/' + p['id'] + '/render', json={'revision': p['revision']}).status_code == 400
    image = io.BytesIO()
    Image.new('RGB', (120, 180), 'orange').save(image, 'PNG')
    asset = client.post('/api/assets', data={'title': '프리뷰 이미지'},
                        files={'file': ('test.png', image.getvalue(), 'image/png')}).json()
    p = client.put('/api/projects/' + p['id'], json={**payload(p),
        'cuts': [{**p['cuts'][0], 'asset_id': asset['id'], 'seconds': 1}]}).json()
    p = approve(client, p)
    result = client.post('/api/projects/' + p['id'] + '/render', json={'revision': p['revision']})
    assert result.status_code == 200, result.text
    state = client.get('/api/state').json()
    assert state['jobs'][0]['status'] == 'complete', state['jobs']
    assert state['videos'][0]['is_preview']
    assert state['videos'][0]['duration'] == 1
    assert client.get('/api/videos/' + state['videos'][0]['id'] + '/file').status_code == 200
