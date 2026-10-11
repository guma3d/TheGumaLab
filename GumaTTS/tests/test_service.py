import json
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import create_app

def setup(tmp_path):
    app = create_app(tmp_path, start_worker=False)
    client = TestClient(app)
    headers = {'Authorization':'Bearer '+(tmp_path/'service-token').read_text()}
    return app,client,headers

def test_auth_and_fail_closed(tmp_path):
    app,c,h = setup(tmp_path)
    assert c.get('/health').status_code == 200
    assert c.get('/api/state').status_code == 401
    assert c.get('/media/unknown/wav').status_code == 401
    assert c.get('/api/state',headers={'Authorization':'Bearer wrong'}).status_code == 401
    assert c.get('/api/state',headers=h).status_code == 200
    with patch('httpx.AsyncClient.get',side_effect=httpx.ConnectError('offline')):
        c.cookies.set('guma_sso_token','test-cookie')
        assert c.get('/api/state').status_code == 401

def test_browser_csrf(tmp_path):
    app,c,h = setup(tmp_path)
    with patch('httpx.AsyncClient.get',return_value=httpx.Response(200)):
        c.cookies.set('guma_sso_token','test-cookie')
        assert c.post('/api/jobs',json={'text':'안녕하세요.'}).status_code == 403
        assert c.post('/api/jobs',json={'text':'안녕하세요.'},headers={'X-GumaTTS':'studio','Origin':'https://evil.example'}).status_code == 403
        assert c.post('/api/jobs',json={'text':'안녕하세요.'},headers={'X-GumaTTS':'studio','Origin':'http://testserver'}).status_code == 202

def test_idempotency_validation_and_versions(tmp_path):
    app,c,h = setup(tmp_path)
    data={'text':'오늘도 좋은 하루 보내세요.'}
    a=c.post('/api/jobs',json=data,headers=h).json()
    b=c.post('/api/jobs',json=data,headers=h).json()
    assert a['id']==b['id']
    changed=c.post('/api/jobs',json={**data,'model':'qwen-0.6b'},headers=h).json()
    assert changed['id']!=a['id']
    assert c.post('/api/jobs',json={**data,'model':'gemini-flash','voice':'Zephyr'},headers=h).status_code==422
    assert c.post('/api/jobs',json={'text':'a'*2001},headers=h).status_code==422
    assert c.get(f'/media/{a["id"]}/wav',headers=h).status_code==409
    assert c.post(f'/api/jobs/{a["id"]}/review',json={'verdict':'approved'},headers=h).status_code==409

def test_ready_media_and_review_history(tmp_path):
    app,c,h=setup(tmp_path)
    job=c.post('/api/jobs',json={'text':'테스트입니다.'},headers=h).json()
    jid=job['id'];folder=tmp_path/jid;folder.mkdir()
    (folder/'original.wav').write_bytes(b'RIFF-test')
    with app.state.store.db() as db:db.execute("UPDATE jobs SET status='ready' WHERE id=?",(jid,))
    assert c.get(f'/media/{jid}/wav',headers=h).content==b'RIFF-test'
    assert c.get(f'/media/{jid}/worker.log',headers=h).status_code==422
    for verdict in ('approved','changes'):
        assert c.post(f'/api/jobs/{jid}/review',json={'verdict':verdict,'note':'억양 확인'},headers=h).status_code==200
    with app.state.store.db() as db:assert db.execute('SELECT count(*) FROM reviews').fetchone()[0]==2
    assert c.get(f'/api/jobs/{jid}',headers=h).json()['review']['scope']=='this_audio_only'

def test_failed_job_can_retry_without_mutating_original(tmp_path):
    app,c,h=setup(tmp_path)
    old=c.post('/api/jobs',json={'text':'재시도'},headers=h).json()
    with app.state.store.db() as db:db.execute("UPDATE jobs SET status='failed' WHERE id=?",(old['id'],))
    new=c.post('/api/jobs',json={'text':'재시도'},headers=h).json()
    assert new['id']!=old['id']
    assert c.get('/api/jobs/'+old['id'],headers=h).json()['status']=='failed'
