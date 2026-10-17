import hashlib
import io
import json
from pathlib import Path
from unittest.mock import patch
import pytest
import client

def test_download_hashes_and_provenance(tmp_path, monkeypatch):
    token=tmp_path/'token';token.write_text('test-token')
    monkeypatch.setenv('GUMATTS_TOKEN_FILE',str(token))
    mp3=b'test-mp3';wav=b'RIFF-test'
    result={'audio_sha256':hashlib.sha256(mp3).hexdigest(),'original_sha256':hashlib.sha256(wav).hexdigest(),'model':'qwen-clone-1.7b','voice':'M5-fixed-v1'}
    def response(req,timeout):
        if req.data:
            payload=json.loads(req.data)
            assert payload['model']=='qwen-clone-1.7b' and payload['voice']=='M5-fixed-v1' and payload['allow_cloud'] is False
        if req.full_url.endswith('/mp3'):return io.BytesIO(mp3)
        if req.full_url.endswith('/wav'):return io.BytesIO(wav)
        return io.BytesIO(json.dumps({'id':'test-job','status':'ready','result':result}).encode())
    with patch('urllib.request.urlopen',side_effect=response):
        out=tmp_path/'voice.mp3'
        data=client.synthesize('테스트',out,model='qwen-clone-1.7b',voice='M5-fixed-v1',project='test')
        assert data['job_id']=='test-job'
        assert out.read_bytes()==mp3
        assert out.with_suffix('.wav').read_bytes()==wav
        assert json.loads(out.with_suffix('.tts.json').read_text())['model']=='qwen-clone-1.7b'
        out.write_bytes(b'original-do-not-overwrite')
        with pytest.raises(FileExistsError):client.synthesize('변경 원고',out,model='qwen-clone-1.7b',voice='M5-fixed-v1',project='test')
        assert out.read_bytes()==b'original-do-not-overwrite'

def test_failed_service_does_not_fallback(tmp_path, monkeypatch):
    token=tmp_path/'token';token.write_text('test-token')
    monkeypatch.setenv('GUMATTS_TOKEN_FILE',str(token))
    with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"id":"failed","status":"failed","error":"quota"}')) as call:
        with pytest.raises(RuntimeError,match='quota'):client.synthesize('원고',tmp_path/'voice.mp3',allow_cloud=True)
        assert call.call_count==1
        assert not (tmp_path/'voice.mp3').exists()

def test_transient_read_retry_keeps_same_job(tmp_path, monkeypatch):
    token=tmp_path/'token';token.write_text('test-token')
    monkeypatch.setenv('GUMATTS_TOKEN_FILE',str(token))
    with patch('urllib.request.urlopen',side_effect=[TimeoutError('connection'),io.BytesIO(b'ready')]) as call, patch('time.sleep'):
        assert client.request('/api/jobs/existing')==b'ready'
        assert call.call_count==2
        assert all(c.args[0].full_url.endswith('/api/jobs/existing') for c in call.call_args_list)
