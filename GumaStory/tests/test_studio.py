import io
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


HEADERS = {'X-GumaStory': 'studio'}


@pytest.fixture
def studio(tmp_path):
    app = create_app(tmp_path, testing=True)
    return TestClient(app), app.state.store


def png():
    output = io.BytesIO()
    Image.new('RGB', (160, 90), '#e3b74b').save(output, format='PNG')
    return output.getvalue()


def upload(client, **fields):
    return client.post('/api/assets/upload', headers=HEADERS,
        data={'title': '테스트 이미지', 'character_id': 'adult-man', **fields},
        files={'file': ('sample.png', png(), 'image/png')})


def test_sso_is_required_for_ui_api_and_originals(tmp_path):
    client = TestClient(create_app(tmp_path), follow_redirects=False)
    assert client.get('/').status_code == 302
    assert client.get('/api/state').status_code == 401
    assert client.get('/media/test/original').status_code == 401
    assert client.get('/health').json()['status'] == 'ok'


def test_mutation_requires_same_origin_header(studio):
    client, _ = studio
    assert client.post('/api/assets/upload').status_code == 403
    assert client.post('/api/assets/upload', headers={**HEADERS, 'Origin': 'https://evil.example'}).status_code == 403


def test_upload_review_archive_and_original_preservation(studio):
    client, store = studio
    first = upload(client).json()
    original = client.get('/media/'+first['id']+'/original').content
    assert original == png()
    assert client.get('/media/'+first['id']+'/thumb').status_code == 200
    review = dict(revision=1, title='검토한 이미지', status='approved', note='손과 표정 확인', tags=['정면'], archived=True)
    assert client.put('/api/assets/'+first['id'], headers=HEADERS, json=review).status_code == 200
    assert client.put('/api/assets/'+first['id'], headers=HEADERS, json=review).status_code == 409
    assert client.get('/media/'+first['id']+'/original').content == original
    second = upload(client, parent_id=first['id']).json()
    assert second['version'] == 2 and second['id'] != first['id']
    assert store.asset(first['id'])['archived']


def test_invalid_files_and_parent_rejected(studio):
    client, _ = studio
    bad = client.post('/api/assets/upload', headers=HEADERS, data={'title':'bad'}, files={'file':('x.png',b'<html>bad</html>','image/png')})
    assert bad.status_code == 422
    assert upload(client, parent_id='missing').status_code == 422


def script_body(client):
    old = client.get('/api/state').json()['scripts'][0]
    return {k:v for k,v in old.items() if k not in ('id','version','saved_at')} | {'expected_version': old['version']}


def test_script_versions_are_immutable_and_stale_writes_fail(studio):
    client, store = studio
    original = store.scripts()[0]
    body = script_body(client)
    body['scenes'][0]['narration'] = '새로운 대본입니다.'
    result = client.post('/api/scripts/promotion', headers=HEADERS, json=body)
    assert result.status_code == 200 and result.json()['version'] == 2
    assert client.post('/api/scripts/promotion', headers=HEADERS, json=body).status_code == 409
    assert next(s for s in store.scripts() if s['version']==1) == original
    assert '새로운 대본' in client.get('/api/scripts/promotion/2/export').text


def test_overlapping_timeline_and_missing_assets_rejected(studio):
    client, _ = studio
    body = script_body(client)
    body['scenes'][1]['start'] = 10
    assert client.post('/api/scripts/promotion', headers=HEADERS, json=body).status_code == 422
    body = script_body(client)
    body['scenes'][0]['asset_ids'] = ['not-found']
    assert client.post('/api/scripts/promotion', headers=HEADERS, json=body).status_code == 422


def test_concurrent_script_saves_do_not_overwrite(studio):
    _, store = studio
    data = {'title':'test','scenes':[]}
    def attempt(_):
        try:
            store.save_script('parallel', 0, data)
            return 'saved'
        except ValueError:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ['conflict','saved']


def test_import_is_idempotent_and_preserves_archives(studio):
    client, store = studio
    (store.root/'assets'/'imported.png').write_bytes(png())
    record=dict(id='imported',file='imported.png',title='import',character_id='boy',kind='angle',version=1,status='review',archived=True)
    (store.root/'imports'/'imported.json').write_text(json.dumps(record),encoding='utf-8')
    for _ in range(2):
        state=client.get('/api/state').json()
    assert len(state['assets']) == 1 and state['assets'][0]['archived'] is True


def test_prefix_links_and_character_master_validation(studio):
    client, _ = studio
    html=client.get('/',headers={'X-Forwarded-Prefix':'/gumastory'}).text
    assert '/gumastory/static/app.js' in html and '__PREFIX__' not in html
    a=upload(client).json()
    wrong=client.put('/api/characters/girl',headers=HEADERS,json={'name':'딸','notes':'','master_id':a['id']})
    assert wrong.status_code == 422
