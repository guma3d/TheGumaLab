import hashlib
import json
import runpy
import sys
import types
from pathlib import Path

import pytest

def test_new_model_cannot_overwrite_previous_production_metadata(tmp_path, monkeypatch):
    root=tmp_path/'version';(root/'voice').mkdir(parents=True)
    (root/'script.json').write_text(json.dumps({'scenes':[{'narration':'원래 문장'}]}))
    audio=root/'voice/001.mp3';audio.write_bytes(b'old-voice')
    audio.with_suffix('.json').write_text(json.dumps({'text_sha256':hashlib.sha256('원래 문장'.encode()).hexdigest(),'model':'gemini-3.8-flash-tts','voice':'Zephyr','audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest()}))
    jobs=root/'voice-jobs.json';jobs.write_bytes(b'previous-manifest')
    async def forbidden(*args,**kwargs):raise AssertionError('Must reject before TTS submission')
    monkeypatch.setitem(sys.modules,'app.core.tts_engine',types.SimpleNamespace(synthesize_speech=forbidden))
    monkeypatch.setattr(sys,'argv',['produce_narration.py',str(root),'qwen-1.7b'])
    with pytest.raises(RuntimeError,match='새 버전'):
        runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/produce_narration.py'),run_name='__main__')
    assert jobs.read_bytes()==b'previous-manifest'
    assert audio.read_bytes()==b'old-voice'
