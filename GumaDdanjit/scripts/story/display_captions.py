"""Editorial display text is independent of immutable TTS narration."""
import re

# Explicit reviewed spellings from promotion v5, not a lossy general Korean parser.
REPLACEMENTS={
 '이천이십육년':'2026년','이천이십삼년':'2023년','이천십구년':'2019년',
 '천백십사 명':'1,114명','백서른한 곳':'131곳',
 '오십사 점 팔 퍼센트':'54.8%','삼 점 삼 퍼센트':'3.3%',
 '사십삼 점 육 퍼센트':'43.6%','칠십육 퍼센트':'76%',
 '이십오 퍼센트':'25%','사십사 퍼센트':'44%','육 퍼센트':'6%','십 퍼센트':'10%',
 '사백사십만 원':'440만 원','사백만 원':'400만 원',
 '이만 오천 원':'25,000원','이만 이천 원':'22,000원',
 '백육십 시간':'160시간','이백 시간':'200시간','한 시간':'1시간','두 달':'2개월',
 '지제트 세대':'Z세대','제트 세대':'Z세대','엠지세대':'MZ세대',
}

def display_text(spoken):
    result=spoken
    for source,target in sorted(REPLACEMENTS.items(),key=lambda pair:len(pair[0]),reverse=True):
        result=re.sub(r'(?<![가-힣A-Za-z0-9])'+re.escape(source),lambda _:target,result)
    return result

def assert_display_numbers(value):
    leftovers=[source for source in REPLACEMENTS if re.search(r'(?<![가-힣A-Za-z0-9])'+re.escape(source),value)]
    if leftovers:raise ValueError(f'Unconverted display numerals: {leftovers}')
    # "몇 퍼센트" is intentionally not a invented numerical result.
    if re.search(r'[일이삼사오육칠팔구십백천]+(?:\s+점\s+[일이삼사오육칠팔구]+)?\s*퍼센트',value):
        raise ValueError('A numerical percentage is still spelled out')
