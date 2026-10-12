from render_motion_revision import char_times,phrase_time

def test_percentage_anchor_does_not_match_year_digit():
    text='이천이십육년 조사, 응답은 육 퍼센트입니다.'
    words=[dict(text='2026년',start=0,end=1),dict(text='조사',start=1,end=2),dict(text='응답은',start=2,end=3),dict(text='6%입니다',start=4,end=5)]
    target,times,_=char_times(text,words,6)
    start,end,ok=phrase_time('육 퍼센트',target,times,6)
    assert ok and 4<=start<end<=5

def test_asr_mixed_numeric_units_keep_spoken_anchor():
    text='시간당 이만 오천 원입니다.'
    words=[dict(text='시간당',start=0,end=1),dict(text='2만',start=1,end=2),dict(text='5천',start=2,end=3),dict(text='원입니다',start=3,end=4)]
    target,times,_=char_times(text,words,4)
    start,end,ok=phrase_time('이만 오천 원',target,times,4)
    assert ok and 1<=start<end<=4
