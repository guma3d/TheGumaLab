import sys
from pathlib import Path
import pytest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import Job, STORY_STYLE
import client

def test_story_cloud_scope_and_opt_in():
    for project in ('story', 'longform'):
        job = Job(text='승진이 확정된 날입니다.', project=project, allow_cloud=True)
        assert (job.model, job.voice, job.style) == ('gemini-flash', 'Zephyr', STORY_STYLE)
        with pytest.raises(ValueError):
            Job(text='원고', project=project)
        for model, voice in [('qwen-clone-1.7b','M5-fixed-v1'), ('gemini-lite','Zephyr')]:
            with pytest.raises(ValueError):
                Job(text='원고', project=project, model=model, voice=voice, allow_cloud=True)

def test_client_story_routes_cloud_without_silent_opt_in():
    with patch.object(client, 'request', return_value=b'{}') as call:
        client.submit('원고', project='story', allow_cloud=True)
        payload = call.call_args.args[1]
        assert (payload['model'], payload['voice'], payload['allow_cloud']) == ('gemini-flash','Zephyr', True)

def test_other_scopes_unchanged():
    assert Job(text='원고', project='test', model='qwen-1.7b').voice == 'Sohee'
    assert Job(text='원고', project='tech').voice == 'F4'
    assert Job(text='원고', project='story_shorts').voice == 'F4'
