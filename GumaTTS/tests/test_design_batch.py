from server import same_local_batch

def test_design_batch_keeps_voice_and_style_boundary():
    cut={'model':'qwen-design-1.7b','voice':'M5','style':'','text':'첫 컷','seed':42}
    assert same_local_batch(cut,{**cut,'text':'다음 컷','seed':43})
    assert not same_local_batch(cut,{**cut,'voice':'F4'})
    assert not same_local_batch(cut,{**cut,'style':'different'})
    assert not same_local_batch(cut,{**cut,'model':'gemini-flash'})

def test_cloud_and_custom_voice_jobs_are_not_batched():
    for model in ('gemini-flash','qwen-1.7b'):
        cut={'model':model,'voice':'test','style':''}
        assert not same_local_batch(cut,cut)
