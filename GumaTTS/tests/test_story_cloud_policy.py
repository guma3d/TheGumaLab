import sys
from pathlib import Path
from unittest.mock import patch
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Job, STYLE
from worker import local_generation
import client

@pytest.mark.parametrize('project',['food','tech','household','video','story','longform','story_shorts'])
def test_native_korean_production_contract(project):
    job=Job(text='편안한 한국어로 읽어요.',project=project)
    assert (job.model,job.voice,job.style)==('qwen-1.7b','Sohee',STYLE)
    repo,method,kwargs=local_generation(job.model_dump())
    assert repo.endswith('1.7B-CustomVoice') and method=='generate_custom_voice'
    assert kwargs['language']=='Korean' and kwargs['speaker']=='Sohee'
    for model,voice in [('qwen-design-1.7b','F4'),('qwen-clone-1.7b','F4-dates-v1'),('gemini-flash','Zephyr')]:
        with pytest.raises(ValueError): Job(text='원고',project=project,model=model,voice=voice,allow_cloud=True)
    with patch.object(client,'request',return_value=b'{}') as call:
        client.submit('원고',project=project)
        payload=call.call_args.args[1]
        assert (payload['model'],payload['voice'],payload['allow_cloud'])==('qwen-1.7b','Sohee',False)
        call.reset_mock()
        with pytest.raises(ValueError):client.submit('원고',project=project,model='gemini-flash',voice='Zephyr',allow_cloud=True)
        call.assert_not_called()

def test_legacy_voice_only_explicit_comparison():
    assert Job(text='과거 참조 비교',project='test',model='qwen-clone-1.7b',voice='F4-dates-v1').voice=='F4-dates-v1'
