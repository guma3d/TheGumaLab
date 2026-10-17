import json
import pytest
from test_service import setup
from server import Job
from voice_profiles import PROFILES, DESIGN_MODEL, DESIGN_REPO
from worker import local_generation

def test_design_checkpoint_and_gender_candidates():
    assert sum(p['gender']=='male' for p in PROFILES.values()) == 5
    assert sum(p['gender']=='female' for p in PROFILES.values()) == 5
    for voice in PROFILES:
        job=Job(text='오늘 출근길은 어땠나요?', model=DESIGN_MODEL, voice=voice)
        repo, method, kwargs=local_generation(job.model_dump())
        assert repo==DESIGN_REPO and method=='generate_voice_design'
        assert 'speaker' not in kwargs and PROFILES[voice]['instruct'] in kwargs['instruct']
        assert kwargs['language']=='Korean'
    with pytest.raises(ValueError): Job(text='안녕', model=DESIGN_MODEL, voice='Sohee')
    with pytest.raises(ValueError): Job(text='안녕', model='qwen-1.7b', voice='M1')
    assert local_generation(Job(text='안녕',model='qwen-0.6b').model_dump())[0].endswith('0.6B-CustomVoice')

def test_comparison_and_immutable_jobs(tmp_path):
    app,c,h=setup(tmp_path)
    a=c.post('/api/jobs',headers=h,json={'text':'같은 글', 'model':DESIGN_MODEL,'voice':'M1'}).json()
    b=c.post('/api/jobs',headers=h,json={'text':'같은 글', 'model':DESIGN_MODEL,'voice':'F1'}).json()
    assert a['id']!=b['id']
    (tmp_path/'voice-comparison-20261011.json').write_text(json.dumps([{'id':a['id']},{'id':b['id']}]))
    state=c.get('/api/state',headers=h).json()
    assert len(state['voice_comparison'])==2 and len(state['voice_profiles'])==10
    assert all(j['review']=={} for j in state['voice_comparison'])


def test_old_reference_is_available_only_for_comparison():
    from fixed_voices import CLONE_MODEL, FOOD_VOICE
    assert FOOD_VOICE == 'F1-bright-v2'
    assert Job(text='이전 참조 비교', project='test', model=CLONE_MODEL,
               voice='F1-fixed-v1').voice == 'F1-fixed-v1'
    with pytest.raises(ValueError):
        Job(text='이전 참조', project='food', voice='F1-fixed-v1')
    with pytest.raises(ValueError):
        Job(text='임의 참조', model=CLONE_MODEL, voice='../../unknown')
