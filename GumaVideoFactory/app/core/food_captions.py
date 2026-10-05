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
Style: Caption,Do Hyeon,57,&H00322528,&H00322528,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,1,4,0,2,90,130,460,1
Style: Headline,Do Hyeon,72,&H00623BD5,&H00623BD5,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,1,5,0,8,90,110,290,1
Style: Ad,Do Hyeon,42,&H00FFFFFF,&H00FFFFFF,&H00322528,&H00322528,-1,0,0,0,100,100,0,0,1,3,0,9,75,95,150,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[f'Dialogue: 3,0:00:00.00,{end},Ad,,0,0,0,,[광고]']
    if headline:
        title=r'\N'.join(_chunks(headline,14))
        lines.append(f'Dialogue: 2,0:00:00.00,{end},Headline,,0,0,0,,{title}')
    chunks=_chunks(text,16);total=sum(map(len,chunks));at=0
    for chunk in chunks:
        until=at+seconds*len(chunk)/total
        lines.append(f'Dialogue: 1,{clock(at)},{clock(until)},Caption,,0,0,0,,{chunk}')
        at=until
    path.write_text(header+'\n'.join(lines)+'\n',encoding='utf-8')
