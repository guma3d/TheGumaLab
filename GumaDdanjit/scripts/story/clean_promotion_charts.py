"""Data-native charts: only the question, values and meaningful comparison labels."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def compose(root, fonts):
    data=json.loads((root.parents[1]/'exports/promotion-v4-charts.json').read_text(encoding='utf-8'))
    cream='#F6F0E4'; navy='#183444'; teal='#267C7B'; gold='#C69227'; pale='#E4E3DA'
    metadata=[]
    for no,item in enumerate(data,1):
        im=Image.new('RGB',(1920,1080),cream);d=ImageDraw.Draw(im);labels=[]
        def text(x,y,value,size=42,color=navy):
            labels.append(value)
            d.text((x,y),value,font=ImageFont.truetype(str(fonts/'Pretendard-SemiBold.otf'),size),fill=color)
        def panel(x,y,w,h):d.rounded_rectangle((x,y,x+w,y+h),24,fill='white')
        values=item['values']
        if no in (1,2):
            text(110,174,'6%와 76%, 왜 이렇게 다를까요?' if no==1 else '임원까지? 다음 승진은?',68)
            if no==1:
                numbers=[values['primary_leadership_goal'],values['future_senior_leadership_interest']]
                names=['리더 지위가 최우선 목표','언젠가 고위 리더 역할에 관심']
            else:
                numbers=[values['no_executive_aspiration'],values['no_promotion_desire']]
                names=['임원까지 갈 생각 없음','승진하고 싶지 않음']
            for x,value,name,color in zip((110,990),numbers,names,(teal,gold)):
                panel(x,340,820,480);text(x+42,390,f'{value}%',138,color);text(x+42,637,name,42)
        elif no==3:
            text(110,174,'책임을 지는 자리가 부담스럽다',68)
            text(110,307,'임원을 원하지 않는 응답자가 꼽은 이유',42)
            value=values['responsibility_burden_among_nonaspirants']
            d.rounded_rectangle((110,489,1810,589),16,fill=pale)
            end=110+1700*value/100;d.rounded_rectangle((110,489,end,589),16,fill=teal)
            text(end+30,485,f'{value}%',72,teal)
            for v in (0,25,50,75,100):text(110+1700*v/100-20,630,f'{v}%',28)
        elif no==4:
            text(110,174,'월급은 올랐는데, 내 시간은?',68)
            panel(110,315,1700,513);cols=(150,870,1360)
            for x,label in zip(cols,('비교 항목','승진 전','승진 후')):text(x,352,label,40)
            rows=[('월 보상',*[f'{v//10000}만 원' for v in values['monthly_pay']]),('일에 쓰는 시간',*[f'{v}시간' for v in values['hours']]),('보상 ÷ 시간',*[f'{v:,}원' for v in values['simple_hourly']])]
            for i,row in enumerate(rows):
                for x,label in zip(cols,row):text(x,455+i*110,label,44,teal if i==2 else navy)
        else:
            text(110,174,'빠르게 오르기, 꾸준히 나아가기',68)
            for y,label,value,color in [(376,'빠른 승진',values['fast_promotions'],gold),(599,'꾸준한 진전',values['steady_progress'],teal)]:
                text(110,y+18,label,44);d.rounded_rectangle((530,y,1780,y+95),16,fill=pale)
                end=530+1250*value/100;d.rounded_rectangle((530,y,end,y+95),16,fill=color);text(end+25,y+6,f'{value}%',59,color)
            for v in (0,25,50,75,100):text(530+1250*v/100-20,752,f'{v}%',28)
        im.save(root/f'charts/{no:02}.png')
        metadata.append(dict(item,chart=no,visible_labels=labels,file=f'charts/{no:02}.png'))
    (root/'chart-provenance.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
