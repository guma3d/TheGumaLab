"""Compose a script-bound 1080p illustrated explainer from approved resources."""
import json, re, shutil, sys, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

root=Path(sys.argv[1]); assets=Path(sys.argv[2]); fonts=Path(sys.argv[3])
script=json.loads((root/'script.json').read_text(encoding='utf-8'))
W,H=1920,1080
C='#F6F0E4';N='#183444';T='#267C7B';Y='#C69227';M='#526776'
out=root/'frames';out.mkdir(exist_ok=True)
maple=fonts/'Maplestory Bold.ttf'; regular=fonts/'Pretendard-SemiBold.otf'
def ft(n,b=True):return ImageFont.truetype(str(maple if b else regular),n)
def wrap(value,width,size=64,b=True):
    lines=[];line=''
    for word in value.split():
        trial=(line+' '+word).strip()
        if ImageDraw.Draw(Image.new('RGB',(1,1))).textlength(trial,font=ft(size,b))>width and line:
            lines.append(line);line=word
        else:line=trial
    if line:lines.append(line)
    return lines
def text(x,y,value,size=60,width=1600,fill=N,b=True):
    for line in wrap(value,width,size,b):
        d.text((x,y),line,font=ft(size,b),fill=fill);y+=size*1.24
    return y
def pic(a,box):
    p=Image.open(assets/(a+'.png')).convert('RGB')
    p=ImageOps.contain(p,(box[2],box[3]),Image.Resampling.LANCZOS)
    im.paste(p,(box[0]+(box[2]-p.width)//2,box[1]+(box[3]-p.height)//2))
def card(title,lines):
    text(100,180,title,80,1650)
    count=len(lines);gap=28;cw=(1720-gap*(count-1))//count
    for k,line in enumerate(lines):
        x=100+k*(cw+gap)
        d.rounded_rectangle((x,395,x+cw,820),radius=30,fill='white')
        d.rounded_rectangle((x,395,x+cw,410),radius=7,fill=T if k%2==0 else Y)
        text(x+35,440,f'{k+1:02}',38,cw-70,M)
        text(x+35,530,line,62 if count<3 else 52,cw-70)
def table(title,rows,headers=('질문','확인할 내용')):
    text(95,180,title,74,1700)
    y=330
    for i,row in enumerate([headers]+rows):
        d.rounded_rectangle((95,y,1825,y+98),radius=12,fill=T if i==0 else 'white')
        text(135,y+24,row[0],36,690,'white' if i==0 else N)
        text(865,y+24,row[1],36,915,'white' if i==0 else N)
        y+=112

headlines=[
['승진이 확정된 날,','인정받았는데, 이직?','축하 메시지 뒤의 질문','실제 조사를 보겠습니다','최우선 목표는 6%','높은 자리는 싫어진 걸까?','그런데, 미래 관심은 76%','6%인데 76%라고요?','질문이 달랐습니다','승진의 조건을 묻다','어떤 자리이기에?'],
['한국 조사로 가보겠습니다','임원과 승진은 다릅니다','변화가 아닌 질문의 차이','임원까지? 다음 직급?','산에 가고 싶은 것과','세 문장은 함께 성립합니다','공포를 대신 진단하지 않기','망설이게 만드는 조건','직함 다음, 책상 위의 일'],
['첫째, 책임의 모양','결정권은 어디에 있나','결과는 팀장 책임','핸들 없는 운전?','책임 부담 43.6%','책임과 함께 주는 것은?','기대만으로는 부족합니다','결정할 수 있는 범위','감정과 조건을 나누기'],
['둘째, 보상의 계산','여기부터는 가상 예시','월 보상 400만 원','440만 원이면 좋아질까?','월 보상과 시간당 보상','계산에 빠진 조건도 있습니다','예측할 수 있는 저녁','시간의 양, 시간의 예측성','같은 제안, 다른 가치','제안의 조건표를 봅시다'],
['셋째, 일의 종류','잘하던 일에서 멀어진다?','레벨 업인데 조작법이 바뀐다','현재 실적과 관리자 적합성','미국 영업직 연구 · 2019','새로운 일은 배워야죠','배울 시간과 도움도 함께','내일부터 맡을 실제 업무','적성과 준비는 다릅니다','직급보다 업무 설명'],
['교육과 멘토, 좋은 출발','원래 하던 일은 누가?','당분간 = 언제까지?','겹침을 끝낼 계획','하루 끝에 시작되는 실무','이미 채워진 컵','누구에게, 언제 넘기는가','사람이 안 오면 무엇을 줄이나','도전의 조건이 달라집니다','학습 부담과 끝없는 누적','새 역할을 해내기 위한 질문'],
['관리자 기피 = 노력 기피?','서로 다른 질문입니다','직함 욕심으로 판단할 수 있을까','열심히에도 여러 뜻이 있습니다','무엇을 평가하는 팀인가','퇴근 시간만으로도 알 수 없습니다','조사가 묻지 않은 것','회사는 무엇을 보상하나요','성과인가, 바쁜 모습인가'],
['반론도 들어보겠습니다','누군가는 팀을 이끌어야 한다','성장에는 낯섦이 있습니다','책임 없는 리더는 어렵습니다','학습 부담인가, 구조의 문제인가','지원하기 어려운 조건 바꾸기','직원도 구체적으로 답하기','협상할 재료를 만듭시다','좋은 관리자와 좋은 조건','매력적인 자리의 조건'],
['빠른 승진 25% · 꾸준한 진전 44%','일부 선택지를 보여줍니다','속도와 방향은 다릅니다','관리자 밖에도 성장이 있습니다','보상을 받으려면 일을 바꿔야 하나','성장의 두 경로','회사마다 현실은 다릅니다','미래를 설명하는 제안','서로 다른 성장을 인정하기'],
['승진 제안서에 네 줄 더','첫 줄 · 책임','둘째 줄 · 결정권','셋째 줄 · 인수인계','넷째 줄 · 평가와 점검','함정이 아니라 업무 설명','빈칸도 일정으로 관리하기','불안을 논의 가능한 조건으로','질문에 답하는 회사인가'],
['두 개의 승진 제안','제안 A · 일단 맡아주세요','제안 B · 조건을 정해봅시다','어느 쪽이 해볼 만한가요','가상 비교입니다','좋은 제안도 거절할 수 있습니다','받아들이는 사람도 있습니다','어떤 선택지를 받았는가','성격 평가에서 일자리 설계로'],
['다시, 승진한 날의 이직 공고','다음 생활을 확인하는 중','서로 다른 질문을 구분하기','평가 대신 조건을 이야기하기','어떤 조건이 설명되지 않았나요','축하할 만한 자리인가요?','여러분은 무엇부터 확인하나요','어떤 조건이면 도전하시겠어요?']]

scene_images={1:['style-00-approved-subway','adult-man-11','adult-man-08'],2:['adult-woman-08','style-03-explainer'],3:['adult-man-11','adult-woman-08'],4:['style-02-home','adult-man-12'],5:['adult-woman-11','adult-man-11'],6:['adult-man-12','adult-woman-12'],7:['adult-woman-12','adult-man-14'],8:['style-01-office','adult-man-11'],9:['adult-woman-15','adult-man-14'],10:['adult-woman-12','style-03-explainer'],11:['adult-man-10','adult-woman-10'],12:['style-00-approved-subway','adult-man-07']}
charts={(1,7):1,(1,8):1,(1,9):1,(2,2):2,(2,3):2,(3,5):3,(4,3):4,(4,4):4,(4,5):4,(4,6):4,(9,1):5,(9,2):5}
cards={
 (1,5):('리더 지위가 최우선 경력 목표',['6%','글로벌 Gen Z\n2026년 조사']),
 (2,4):('같은 승진, 다른 질문',['임원까지 가고 싶은가','다음 직급으로 가고 싶은가']),
 (2,6):('함께 성립하는 세 가지',['실력을 인정받고 싶다','소득을 높이고 싶다','임원은 목표가 아니다']),
 (3,2):('가상 업무 상황',['일정은 책임진다','충원은 승인받는다','우선순위는 누가?']),
 (3,6):('확인할 질문',['맡아야 할 책임','행사할 결정권']),
 (3,8):('어디까지 결정할 수 있나요?',['업무 우선순위','인력과 일정','예산과 범위']),
 (4,8):('시간의 조건',['얼마나 일하는가','언제 일할지 아는가']),
 (5,3):('새 역할, 새로운 능력',['내가 잘하는 일','팀이 잘하게 만드는 일']),
 (5,4):('연구가 짚은 긴장',['현재 업무 실적','관리자 역할 적합성']),
 (5,8):('새 역할의 업무',['사람을 키우기','갈등을 조율하기','팀 결과로 평가받기']),
 (5,9):('다르게 확인할 두 가지',['하고 싶은가 · 적성','준비됐는가 · 학습']),
 (6,3):('당분간, 언제까지인가요?',['시작 날짜','종료 날짜','인수인계 담당']),
 (6,7):('지원 계획의 세 칸',['누구에게','언제까지','무엇을 넘기는가']),
 (6,8):('충원이 늦어진다면?',['일은 그대로?','우선순위 조정?','업무량 조정?']),
 (6,10):('부담에도 차이가 있습니다',['배워야 할 낯섦','끝없이 쌓이는 일']),
 (7,2):('별개로 확인해야 합니다',['리더십 역할 선호','실제 업무 성실성']),
 (7,4):('열심히 일한다는 것',['문제를 풀기','실수를 줄이기','다시 일하지 않게 기록']),
 (7,5):('가상의 두 팀',['늦게까지 남았는가','문제를 개선했는가']),
 (7,8):('우리는 무엇을 보상하나요?',['시간','직함에 대한 욕심','실제 결과']),
 (8,5):('구분하면 대화가 시작됩니다',['배울 수 있는 부담','바꿔야 하는 구조']),
 (8,7):('직원에게 남는 질문',['어떤 조건이면?','무엇을 배울까?','어디까지 감수할까?']),
 (8,9):('함께 필요한 두 가지',['좋은 관리자','도전할 만한 조건']),
 (9,3):('성장의 속도와 방향',['빠르게 오르기','깊게 배우기']),
 (9,6):('편집자 제안 · 성장의 경로',['사람을 이끄는 성장','전문성을 쌓는 성장']),
 (10,1):('승진 제안서',['책임과 결정권','인수인계','평가와 점검']),
 (10,2):('무엇을 책임집니까?',['납기','품질','사람의 성장']),
 (10,3):('무엇을 결정할 수 있습니까?',['업무 배분','요청의 우선순위','예산 범위']),
 (10,4):('기존 업무는 어떻게 넘깁니까?',['담당자','인수인계 날짜','충원 지연 대안']),
 (10,5):('학습 기간을 어떻게 다룹니까?',['초기 목표','도움을 받을 사람','다시 점검할 날짜']),
 (11,8):('선택 전에 있었던 것',['무슨 선택을 했나','어떤 선택지를 받았나']),
 (12,4):('이제 조건을 이야기해 봅시다',['책임과 권한','보상과 시간','업무와 지원']),
 (12,7):('무엇부터 확인하시겠습니까?',['월급과 결정권','인수인계','예측할 수 있는 저녁'])}
tables={
 (6,5):('가상 일정 · 관리 뒤에 남은 실무',[('오전','팀 회의'),('오후','면담과 다른 부서 조율'),('하루 끝','기존 실무 시작')]),
 (10,6):('함께 확인하는 네 줄',[('책임','무엇을 먼저 지킬 것인가'),('권한','어디까지 결정할 것인가'),('인수인계','누가 언제 넘겨받는가'),('평가·점검','학습 기간을 어떻게 볼 것인가')]),
 (11,2):('가상 제안 A',[('기존 업무','당분간 병행'),('추가 인력','나중에 논의'),('문제 발생','알아서 해결')]),
 (11,3):('가상 제안 B',[('기존 업무','날짜를 정해 인계'),('결정권','우선순위 조정'),('적응 지원','정기 점검과 초기 목표')]),
 (11,4):('같은 직급·보상, 다른 조건',[('제안 A','범위와 지원이 모호함'),('제안 B','인계·권한·지원이 명확함')])}

plan=[]
for si,scene in enumerate(script['scenes'],1):
    paras=scene['narration'].split('\n\n');assert len(paras)==len(headlines[si-1])
    for pi,p in enumerate(paras,1):
        idx=len(plan)+1;headline=headlines[si-1][pi-1];key=(si,pi)
        im=Image.new('RGB',(W,H),C);d=ImageDraw.Draw(im)
        image_id='';kind='illustration';source=''
        if key in charts:
            image_id=f'promotion-v4-ch{charts[key]:02}';kind='chart'
            pic(image_id,(115,0,1690,905))
        elif key in cards:
            kind='diagram';title,lines=cards[key];card(title,lines)
        elif key in tables:
            kind='table';title,rows=tables[key];table(title,rows)
        else:
            choices=scene_images[si];image_id=choices[(pi-1)%len(choices)]
            if pi in (1,6) or si==12 and pi<=2:
                # Fixed composition, no zoom or pan. Caption-safe lower space.
                pic(image_id,(0,0,1920,1080))
                overlay=Image.new('RGBA',(W,H));g=ImageDraw.Draw(overlay)
                for y in range(360):g.line((0,y,W,y),fill=(18,36,45,max(0,185-int(y*.51))))
                im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB');d=ImageDraw.Draw(im)
                text(90,145,headline,74,1710,'white');kind='full-illustration'
            else:
                pic(image_id,(60,225,1160,652))
                text(1280,265,headline,62,545)
                d.rounded_rectangle((1280,650,1745,661),radius=5,fill=T)
                text(1280,705,'승진의 조건',30,500,M,False)
        if kind!='chart':
            color='white' if kind=='full-illustration' else M
            text(90,46,f'{si:02}  /  {scene["title"]}',31,1630,color,False)
            text(1765,46,f'{si}/12',27,150,color,False)
        if key==(1,1):text(95,830,'설명용 가상 장면',27,1000,'white',False)
        if key==(1,5):source='Deloitte 2026 · 44개국 Gen Z 14,384명 · 최우선 목표 문항'
        if key==(5,4):source='Benson·Li·Shue (2019), QJE · 미국 영업직 · 131개 기업'
        if image_id=='adult-woman-11':source='설명용 일러스트 · 배경 그래픽은 조사 데이터가 아닙니다'
        if kind in ('diagram','table') and not source:source='설명용 도식 · 편집자 해석 / 가상 예시'
        if source:text(100,872,source,24,1710,'white' if kind=='full-illustration' else M,False)
        # Thin chapter strip at bottom; captions have reserved y=940..1040.
        d.rectangle((0,1071,int(W*idx/114),1079),fill=T)
        file=out/f'{idx:03}.png';im.save(file)
        plan.append(dict(index=idx,scene=si,paragraph=pi,headline=headline,kind=kind,image_id=image_id,file=f'frames/{idx:03}.png',text=p,frame_sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
(root/'visual-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
# All cuts, contact sheets are evidence only, not replacement for full-size inspection.
for page in range((len(plan)+19)//20):
    sheet=Image.new('RGB',(1920,1180),C);dd=ImageDraw.Draw(sheet)
    for i,item in enumerate(plan[page*20:page*20+20]):
        p=Image.open(root/item['file']).resize((384,216))
        x=(i%5)*384;y=(i//5)*295;sheet.paste(p,(x,y));dd.text((x+8,y+220),f'{item["index"]:03} / {item["kind"]}',fill=N,font=ft(18,False))
    sheet.save(root/f'contact-{page+1:02}.jpg',quality=90)
print(json.dumps({'frames':len(plan),'contact_sheets':(len(plan)+19)//20}))
