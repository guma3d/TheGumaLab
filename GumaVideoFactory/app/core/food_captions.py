"""Stable food captions: clear hierarchy, quiet badges and readable Korean type."""
import re


def _chunks(text, limit):
    words=re.sub(r'[{}\\\r\n]',' ',text).split()
    lines=[]; line=''
    for word in words:
        for part in [word[i:i+limit] for i in range(0,len(word),limit)]:
            if line and len(line)+len(part)+1>limit:
                lines.append(line);line=''
            line=(line+' '+part).strip()
    if line:lines.append(line)
    return lines or [' ']


def write_food_captions(path,text,seconds,headline,generated=False):
    def clock(t):
        cs=round(t*100)
        return f'{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}'
    end=clock(seconds)
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Pretendard,57,&H00322528,&H00322528,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,16,0,2,90,130,460,1
Style: Headline,Pretendard ExtraBold,72,&H00623BD5,&H00623BD5,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,90,110,290,1
Style: Ad,Pretendard,42,&H00FFFFFF,&H00FFFFFF,&H00322528,&H00322528,-1,0,0,0,100,100,0,0,3,10,0,9,75,95,150,1
Style: Disclosure,Pretendard,29,&H00FFFFFF,&H00FFFFFF,&H00322528,&H00322528,0,0,0,0,100,100,0,0,3,7,0,2,65,110,235,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[f'Dialogue: 3,0:00:00.00,{end},Ad,,0,0,0,,[광고]',
        f'Dialogue: 3,0:00:00.00,{end},Disclosure,,0,0,0,,이 포스팅은 쿠팡 파트너스 활동의 일환으로,\\N이에 따른 일정액의 수수료를 제공받습니다.']
    if generated:
        lines.append(f'Dialogue: 2,0:00:00.00,{end},Disclosure,,0,0,335,,AI 연출 이미지·영상')
    if headline:
        title=r'\N'.join(_chunks(headline,14))
        lines.append(f'Dialogue: 2,0:00:00.00,{end},Headline,,0,0,0,,{title}')
    chunks=_chunks(text,16);total=sum(map(len,chunks));at=0
    for chunk in chunks:
        until=at+seconds*len(chunk)/total
        lines.append(f'Dialogue: 1,{clock(at)},{clock(until)},Caption,,0,0,0,,{chunk}')
        at=until
    path.write_text(header+'\n'.join(lines)+'\n',encoding='utf-8')
