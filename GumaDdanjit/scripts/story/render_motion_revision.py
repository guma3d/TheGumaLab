"""Speech-timed motion graphics for immutable promotion v5; render per-cut and preserve stems."""
import argparse,hashlib,json,math,re,subprocess,time,wave
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from difflib import SequenceMatcher
from PIL import Image,ImageDraw,ImageFont,ImageOps
from promotion_motion_editorial import editorial
from display_captions import display_text,assert_display_numbers
W,H,FPS=1920,1080,30
CREAM='#F5F0E5';NAVY='#163544';TEAL='#248D91';GOLD='#D59B35';CORAL='#DE705A'
FONTS=Path('/app/app/assets/fonts')
def font(size,display=False):return ImageFont.truetype(str(FONTS/('DoHyeon-Regular.ttf' if display else 'Pretendard-SemiBold.otf')),size)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(f'FFmpeg exit {p.returncode}: '+p.stderr[-4000:])
    return p
def norm(s):return re.sub('[^가-힣a-zA-Z0-9]','',s).lower()
class AlignedText(str):pass
def lines(text,ft,maxw):
    rows=['']
    for word in text.split():
        trial=(rows[-1]+' '+word).strip()
        if ft.getlength(trial)>maxw and rows[-1]:rows.append(word)
        else:rows[-1]=trial
    return rows
def write(d,xy,text,size,color=NAVY,width=1600,display=False):
    ft=font(size,display);xx,yy=xy
    for row in lines(text,ft,width):d.text((xx,yy),row,font=ft,fill=color);yy+=int(size*1.25)
    return yy
def char_times(expected,words,duration):
    # Map displayed numeral spellings to ASR characters. Each word's internal timing is approximate.
    display=display_text(expected);target=AlignedText(norm(display));target.display=display;chars='';times=[]
    for word in words:
        value=norm(display_text(word['text']))
        for k,c in enumerate(value):
            chars+=c;times.append((word['start']+(word['end']-word['start'])*k/max(1,len(value)),word['start']+(word['end']-word['start'])*(k+1)/max(1,len(value))))
    for source,replacement in [('2만5천','25000'),('2만2천','22000')]:
        while source in chars:
            ix=chars.index(source);span=times[ix:ix+len(source)];a,b=span[0][0],span[-1][1]
            chars=chars[:ix]+replacement+chars[ix+len(source):]
            times=times[:ix]+[(a+(b-a)*k/len(replacement),a+(b-a)*(k+1)/len(replacement)) for k in range(len(replacement))]+times[ix+len(source):]
    aligned={}
    for m in SequenceMatcher(None,target,chars,autojunk=False).get_matching_blocks():
        for k in range(m.size):aligned[m.a+k]=times[m.b+k]
    return target,aligned,len(aligned)/max(1,len(target))
def phrase_time(phrase,target,aligned,duration,default=.2):
    display_phrase=display_text(phrase);key=norm(display_phrase)
    rawpos=target.display.find(display_phrase)
    pos=len(norm(target.display[:rawpos])) if rawpos>=0 else target.find(key)
    if pos<0:return default,min(duration,default+1),False
    values=[aligned[k] for k in range(pos,pos+len(key)) if k in aligned]
    if not values:return default,min(duration,default+1),False
    return min(x[0] for x in values),max(x[1] for x in values),len(values)>=max(1,len(key)*.7)
def fraction_time(f,target,aligned,duration):
    ix=min(len(target)-1,max(0,int(f*len(target))))
    nearby=sorted(aligned,key=lambda k:abs(k-ix))
    return aligned[nearby[0]][0] if nearby else f*duration
CONCEPTS={15:['임원까지','다음 직급'],17:['인정','보상','임원 목표는 별개'],22:['일정 책임','우선순위는 위에서','충원은 승인 필요','마감은 고정'],26:['책임','권한','자원'],28:['책임감?','결정권은 어디까지?'],37:['더 나은 보상','예측 가능한 저녁'],42:['나의 성과','팀이 잘하게 하는 일'],43:['현재 실적','관리 적합성'],47:['사람을 키우기','갈등 중재','팀 결과로 평가'],48:['적성','준비'],52:['당분간','종료일은?'],54:['팀 회의','면담·조율','퇴근 직전 실무'],56:['누구에게?','언제까지?','충원이 늦으면?'],57:['인력 없음','업무 그대로','기대 결과 그대로'],59:['성장의 부담','끝없는 누적'],62:['리더 역할 선호','일하는 태도'],64:['시간','문제 해결','실수 줄이기','기록'],65:['늦은 퇴근','반복 문제 해결'],68:['바쁜 모습','큰 직함','실제 결과'],74:['낯선 업무','결정권 없는 책임'],76:['시도할 조건','부족한 능력','학습 부담'],78:['좋은 관리자','관리자가 될 조건'],82:['속도','방향'],85:['리더의 성장','전문성의 성장'],89:['책임','결정권','업무 이관','적응·평가'],90:['납기','품질','사람 성장'],91:['업무 배분','요청 거절','예산'],92:['누구에게','언제까지','충원 지연 시'],93:['적응 목표','배움','다시 점검'],94:['책임','권한','업무 이관','적응·평가'],99:['기존 업무 병행','충원은 나중에','알아서 해결'],100:['이관 날짜','우선순위 권한','정기 점검','적응 목표'],101:['어려운 결정','혼자 버티는가?'],105:['무슨 선택?','어떤 선택지?'],110:['책임·권한','보상·시간','업무·지원'],113:['월급','권한','업무 이관','예측 가능한 저녁']}
CHARTS={5:1,7:1,8:1,9:1,13:2,14:2,25:3,32:4,33:4,34:4,35:4,80:5,81:5}
KEYWORDS={2:['인정과 월급 인상','다른 회사의 채용 공고'],3:['축하받을 일','복잡해진 마음'],4:['어쩌다 이런 고민이?','숫자부터 확인'],10:['승진이 싫다?','승진의 조건이 별로다?'],11:['욕심이 없는 걸까?','욕심이 나지 않는 자리'],16:['주말 등산','전문 산악인의 목표'],18:['두려움을 단정하기 전에','조사가 실제로 묻는 것'],19:['올라가고 싶은 마음','멈칫하게 만드는 조건'],24:['책임은 내 몫','핸들은 다른 사람에게'],29:['실패가 두렵다','실패를 막을 수 없는 자리'],30:['회사는 비용을 계산','직원도 시간을 계산'],36:['미리 아는 1시간','언제 생길지 모르는 1시간','예측 가능한 저녁'],38:['지금 필요한 소득','가족을 돌볼 시간'],39:['거절했다는 한 줄','그 사람이 받은 조건표'],40:['잘해서 승진했는데','잘하던 일에서 멀어진다'],41:['디자인 실력','면담 · 평가 · 회의','결과물 대신 갈등 조율'],44:['미국 영업직 연구','한국 모든 직무의 답은 아님'],46:['새 역할을 배우려면','시간과 도움도 함께'],49:['직급과 연봉','내일부터 실제로 할 일'],53:['인수인계의 시간','업무 겹침의 종료 계획'],55:['가득 찬 컵','물을 덜 붓거나 다른 컵'],58:['이관 날짜 · 목표 조정','함께 문제를 풀 선배'],60:['요령을 피우는 질문?','실제로 해내기 위한 질문'],63:['깊어지는 기술','원하지 않을 수 있는 인사 평가','직함보다 일하는 태도'],66:['일찍 퇴근 = 성과?','시간 하나로 판정하지 않기'],67:['리더십과 경력 응답','성실함의 성적표는 아님'],69:['일을 고치기','바쁜 모습을 보이기'],71:['일정 · 결정 · 교육','관리자의 일은 필요'],72:['처음에는 불편합니다','도전이 만드는 선택지'],73:['판단과 책임','모든 부담을 없앨 수는 없죠'],75:['개인의 패기','지원하기 어려운 조건'],77:['구체적인 조건','협상할 재료'],79:['매력적인 자리를 만들려면','무엇을 보여줘야 할까요?'],83:['프로젝트 완성','새 기술 · 넓은 경험','이것도 성장 아닌가요?'],84:['잘하는 일을 계속하기','보상을 받기 위한 다른 역할'],86:['여러 역할을 겸한다면','평가 기준을 분명하게'],87:['무작정 믿으라는 제안','다음 일을 설명하는 제안'],88:['더 높은 자리','더 깊은 전문성'],95:['모르는 부분은 모른다고','언제 결정할지 정하기'],96:['막연한 불안','논의 가능한 조건'],97:['조건을 맞춰보는가','질문을 충성심으로 보는가'],103:['건강과 지금의 우선순위','다른 전문 분야의 선택'],104:['기회를 만드는 사람','그래도 설명해야 할 조건'],106:['세대의 성격 평가','일자리의 설계'],108:['인정받기 싫은 걸까요?','다음 생활을 확인하는 중'],111:['왜 망설이나요?','설명되지 않은 조건은?'],114:['누가 더 열심히 사나?','어떤 조건이면 도전할까?','승진이 다시 기대되려면']}
def card(path,text,width,height,color='white',ink=NAVY,sz=55):
    im=Image.new('RGBA',(width,height));d=ImageDraw.Draw(im);d.rounded_rectangle((0,0,width-1,height-1),radius=25,fill=color)
    d.rounded_rectangle((0,0,10,height-1),radius=5,fill=TEAL)
    ft=font(sz,True)
    while (len(lines(text,ft,width-70))*int(sz*1.25)>height-40 or any(ft.getlength(x)>width-70 for x in lines(text,ft,width-70))) and sz>30:sz-=2;ft=font(sz,True)
    rows=lines(text,ft,width-70);yy=(height-len(rows)*sz*1.25)/2
    for row in rows:d.text((35,yy),row,font=ft,fill=ink);yy+=sz*1.25
    im.save(path)
def draw_count(value,unit,onset,length,x,y,size=90,color=TEAL):
    unit=unit.replace('%',r'\\%')
    progress=f'clip((t-{onset:.5f})/{length:.5f},0,1)'
    if abs(value-round(value))>.01:
        amount=round(value*10)
        text=f'%{{eif\\:floor({amount}*{progress}/10)\\:d}}.%{{eif\\:mod(floor({amount}*{progress}),10)\\:d}}{unit}'
    else:text=f'%{{eif\\:floor({round(value)}*{progress}+0.00001)\\:d}}{unit}'
    # Commas inside expressions must survive FFmpeg's filter-list parser.
    text=text.replace(',',r'\,')
    return f"drawtext=fontfile={FONTS}/DoHyeon-Regular.ttf:text='{text}':fontsize={size}:fontcolor={color}:x={x}:y={y}"
def prepare_cut(root,cut,voice,asr,old,ed):
    n=cut['index'];folder=root/'motion'/f'{n:03}';folder.mkdir(parents=True,exist_ok=True)
    target,aligned,coverage=char_times(voice['text'],asr['words'],asr['duration']);duration=cut['duration']
    is_image='illustration' in old['kind'];chart=CHARTS.get(n)
    if is_image:
        base=Image.open(root.parent/'promotion-v4'/old['file']).convert('RGB')
    else:
        base=Image.new('RGB',(W,H),CREAM);d=ImageDraw.Draw(base)
        d.ellipse((1510,-230,2190,450),fill='#ECE5D5');d.ellipse((-210,680,190,1080),fill='#E4EDE7')
        d.rectangle((0,934,W,H),fill=NAVY)
    layers=[];numbers=[];countfilters=[]
    # 2026-10-13: no standalone keyword/headline animation. Chart context stays static.
    if chart:
        header=folder/'header.png';card(header,ed['headline'],1720,145,color=(255,255,255,245),ink=NAVY,sz=72)
        base.paste(Image.open(header),(100,155),Image.open(header))
    def number(value,unit,phrase,x,y,size=90,bar=None,static=False):
        a,b,ok=phrase_time(phrase,target,aligned,asr['duration'])
        if not static and not ok:raise ValueError(f'Numeric voice anchor missing: cut {n}, {phrase}')
        onset=0 if static else max(0,a-.65);length=.001 if static else max(.4,b-onset)
        countfilters.append(draw_count(value,unit,onset,length,x,y,size))
        numbers.append(dict(value=value,unit=unit,spoken_phrase=phrase,spoken_start=a,spoken_end=b,start=onset,end=onset+length,anchor_aligned=ok,static=static,x=x,y=y))
        if bar:
            px,py,width=bar;im=Image.new('RGBA',(max(2,round(width)),58),TEAL);name=f'bar-{len(numbers)}.png';im.save(folder/name)
            layers.append(dict(file=name,x=px,y=py,start=onset,end=duration,role='bar',grow_seconds=length,target_width=width,static=static))
    if chart:
        d=ImageDraw.Draw(base)
        if chart==1:
            for i,(label,value,phrase) in enumerate([('리더 지위가 최우선 목표',6,'육 퍼센트'),('언젠가 고위 리더 역할에 관심',76,'칠십육 퍼센트')]):
                if n==5 and i==1:continue
                xx=120+i*860;d.rounded_rectangle((xx,360,xx+810,825),30,fill='white');write(d,(xx+42,400),label,44,width=730)
                number(value,'%',phrase,xx+45,515,142,static=(n==9 or (n==7 and i==0)))
            write(d,(130,865),'2026년 글로벌 Z세대 · 서로 다른 문항',32,color=NAVY)
        elif chart in (2,3,5):
            if chart==2:rows=[('임원까지 갈 생각 없음',54.8,'오십사 점 팔 퍼센트'),('승진하고 싶지 않음',3.3,'삼 점 삼 퍼센트')];scope='2023년 국내 MZ 직장인 조사 · 별도 문항'
            elif chart==3:rows=[('책임지는 자리가 부담스럽다',43.6,'사십삼 점 육 퍼센트')];scope='임원을 희망하지 않은 응답자 안에서 · 전체 청년 비율 아님'
            else:rows=[('빠른 승진 선호',25,'이십오 퍼센트'),('꾸준한 진전 선호',44,'사십사 퍼센트')];scope='2026년 글로벌 Z세대 · 일부 선택지만 표시'
            for i,(label,value,phrase) in enumerate(rows):
                yy=430+i*210;write(d,(125,yy-55),label,46,width=1450)
                d.rounded_rectangle((125,yy+40,1455,yy+98),15,fill='#DDDCCD')
                for tick in (0,25,50,75,100):
                    xx=125+1330*tick/100;d.line((xx,yy+101,xx,yy+115),fill='#9CAAA9',width=2)
                    write(d,(xx-20,yy+122),str(tick)+'%',25)
                number(value,'%',phrase,1490,yy+7,84,bar=(125,yy+40,1330*value/100),static=n in (14,81))
            write(d,(125,863),scope,31,width=1710)
        else:
            d.rounded_rectangle((110,337,1810,820),25,fill='white');write(d,(135,358),'비교 항목',37);write(d,(845,358),'승진 전',37);write(d,(1350,358),'승진 후',37)
            for i,label in enumerate(['월 보상','일에 쓰는 시간','보상 ÷ 시간']):write(d,(140,460+i*111),label,43,color=TEAL if i==2 else NAVY)
            before=[(400,'만 원','사백만 원'),(160,'시간','백육십 시간'),(25000,'원','이만 오천 원')]
            after=[(440,'만 원','사백사십만 원'),(200,'시간','이백 시간'),(22000,'원','이만 이천 원')]
            for i,(value,unit,phrase) in enumerate(before):number(value,unit,phrase,845,454+i*111,56,static=n!=32)
            if n>=33:
                for i,(value,unit,phrase) in enumerate(after):number(value,unit,phrase,1350,454+i*111,56,static=n!=33)
            else:
                for i in range(3):write(d,(1350,454+i*111),'—',56,color='#A7B4B5')
            if n==33:
                badge=folder/'pay-badge.png';card(badge,'월 보상 +10%',490,90,color=TEAL,ink='white',sz=48)
                a,b,ok=phrase_time('십 퍼센트',target,aligned,asr['duration']);assert ok
                base.paste(Image.open(badge),(1250,835),Image.open(badge))
            elif n in (34,35):
                badge=folder/'time-badge.png';card(badge,'시간을 기준으로 다시 보기',920,90,color=TEAL,ink='white',sz=46)
                base.paste(Image.open(badge),(885,838),Image.open(badge))
            write(d,(130,857),'월 보상 ÷ 일에 쓰는 시간',31,width=950)
    elif not is_image:
        values=CONCEPTS.get(n,[ed['headline']]);k=len(values);cw=int((1720-(k-1)*22)/k)
        for i,concept in enumerate(values):
            name=f'concept-{i}.png';card(folder/name,concept,cw,280,color='white',sz=60 if k<3 else 50)
            # Explanatory diagrams remain still; never reveal caption-like phrases as motion.
            im=Image.open(folder/name);base.paste(im,(100+i*(cw+22),430),im)
    if is_image:
        # Reframe genuine scene illustrations; never substitute character-reference portraits.
        motion=dict(zoom_start=1.025,zoom_end=1.09,pan_direction='left' if n%2 else 'right')
    else:motion=dict(zoom_start=1,zoom_end=1,pan_direction=None)
    base.save(folder/'base.png');save(folder/'motion.json',dict(index=n,duration=duration,layers=layers,numbers=numbers,motion=motion,asr_character_coverage=coverage,source_frame_sha256=old['frame_sha256'],caption_font_size=50.6))
    return folder,countfilters
def ass_time(t):
    n=round(t*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
def vtt_time(t):
    n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02}.{n%1000:03}'
ASS='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Pretendard SemiBold,50.6,&H00FFFFFF,&H00FFFFFF,&H00201912,&H70000000,0,0,0,0,100,100,0,0,1,1.3,0.4,2,120,120,48,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
def captions(root,cut,asr,ed):
    target,aligned,cov=char_times(asr['expected'],asr['words'],asr['duration']);cues=[];events=[];ft=font(50.6)
    # Editorial cues follow sequential source meaning; assign source character spans using shared phrases.
    source_sentences=[s for s in re.split(r'(?<=[.!?])\s+',display_text(asr['expected'])) if s.strip()]
    count=len(ed['captions']);fractions=[0]
    for i in range(1,count):
        if len(source_sentences)<count:fractions.append(i/count)
        else:
            ideal=int(i*len(source_sentences)/count);prefix=''.join(source_sentences[:ideal]);fractions.append(len(norm(prefix))/max(1,len(target)))
    fractions.append(1)
    for i,value in enumerate(ed['captions']):
        assert_display_numbers(value);rows=lines(value,ft,1620);assert len(rows)<=2,(cut['index'],value,rows)
        start=max(.02,fraction_time(fractions[i],target,aligned,asr['duration']))
        end=fraction_time(fractions[i+1],target,aligned,asr['duration']) if i+1<count else asr['duration']
        if i==0:start=.03
        assert end>start+.12,(cut['index'],start,end)
        text='\n'.join(rows);cues.append(dict(index=cut['index'],start=cut['start']+start,end=cut['start']+end,text=text,local_start=start,local_end=end))
        safe=text.replace('\n',r'\N').replace('{','').replace('}','')
        events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{safe}')
    folder=root/'motion'/f'{cut["index"]:03}';(folder/'captions.ass').write_text(ASS+'\n'.join(events)+'\n')
    return cues
def encode_cut(root,cut,folder,countfilters,preview=False):
    cfg=json.loads((folder/'motion.json').read_text());duration=cut['duration'];frames=round(duration*FPS)
    out=root/'segments'/f'{cut["index"]:03}.mp4';out.parent.mkdir(exist_ok=True)
    logic=root/'renderer-logic-v1.py'
    fingerprint=sha(folder/'motion.json')+sha(folder/'captions.ass')+sha(folder/'base.png')+sha(logic if logic.exists() else Path(__file__))
    if any(x.get('grow_seconds') for x in cfg['layers']):fingerprint+='fixed-rgba-growth-v3'
    composite=sum(x['role']=='concept' for x in cfg['layers'])>=4
    if composite:fingerprint+='single-rgba-composite-v1'
    marker=out.with_suffix('.json')
    if not preview and marker.exists() and out.exists():
        prior=json.loads(marker.read_text())
        if prior['inputs']==fingerprint and prior['sha256']==sha(out) and not prior.get('preview'):return out
    if composite:
        ui=folder/'ui-composite.mov';images=[Image.open(folder/x['file']).convert('RGBA') for x in cfg['layers']]
        process=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','qtrle',str(ui)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        for frame_index in range(frames):
            t=frame_index/FPS;frame=Image.new('RGBA',(W,H))
            for layer,image in zip(cfg['layers'],images):
                if not layer['start']<=t<=layer['end']:continue
                if layer.get('grow_seconds'):
                    progress=1 if layer.get('static') else max(0,min(1,(t-layer['start'])/layer['grow_seconds']));visible=round(image.width*progress)
                    if visible:frame.alpha_composite(image.crop((0,0,visible,image.height)),(layer['x'],layer['y']))
                else:
                    opacity=max(0,min(1,(t-layer['start'])/.35));im=image.copy();im.putalpha(im.getchannel('A').point(lambda a:round(a*opacity)))
                    offset=28*(1-max(0,min(1,(t-layer['start'])/.5))**.7);frame.alpha_composite(im,(layer['x'],round(layer['y']+offset)))
            process.stdin.write(frame.tobytes())
        process.stdin.close();error=process.stderr.read();assert process.wait()==0,error.decode()
        graph=f'[0:v][1:v]overlay=0:0:eof_action=repeat,ass={folder}/captions.ass:fontsdir={FONTS}[c];[c][2:v]overlay=0:0:shortest=0,format=yuv420p[v]'
        run(['ffmpeg','-v','error','-y','-threads','1','-loop','1','-framerate','30','-i',str(folder/'base.png'),'-threads','1','-i',str(ui),'-threads','1','-loop','1','-framerate','30','-i',str(root/'logo-layer.png'),'-filter_complex_threads','1','-filter_complex',graph,'-map','[v]','-an','-frames:v',str(frames),'-r','30','-c:v','libx264','-preset','veryfast','-crf','21','-threads','4','-movflags','+faststart',str(out)])
        save(marker,dict(inputs=fingerprint,frames=frames,sha256=sha(out),preview=preview,composition='one fixed-size RGBA UI stream'))
        return out
    args=['ffmpeg','-v','error','-y','-threads','2','-loop','1','-framerate','30','-i',str(folder/'base.png')]
    for layer in cfg['layers']:
        if layer.get('grow_seconds'):
            # Fixed dimensions avoid retaining a new scaler buffer pool for every growth frame.
            image=Image.open(folder/layer['file']).convert('RGBA');clip=folder/(Path(layer['file']).stem+'.mov')
            length=layer['grow_seconds'];total=max(2,round(duration*FPS))
            command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{image.width}x{image.height}','-r','30','-i','pipe:0','-an','-c:v','qtrle',str(clip)]
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
            for frame_index in range(total):
                progress=1 if layer.get('static') else max(0,min(1,(frame_index/FPS-layer['start'])/length))
                frame=Image.new('RGBA',image.size);visible=round(image.width*progress)
                if visible:frame.paste(image.crop((0,0,visible,image.height)),(0,0))
                process.stdin.write(frame.tobytes())
            process.stdin.close();error=process.stderr.read();assert process.wait()==0,error.decode()
            args+=['-i',str(clip)]
        else:args+=['-loop','1','-framerate','30','-i',str(folder/layer['file'])]
    args+=['-loop','1','-framerate','30','-i',str(root/'logo-layer.png')]
    graph=[];motion=cfg['motion'];node='b0'
    if motion['zoom_end']>1:
        ratio=f'on/{max(1,frames-1)}';zoom=f'{motion["zoom_start"]}+({motion["zoom_end"]}-{motion["zoom_start"]})*{ratio}'
        x=f'(iw-iw/zoom)*({ratio})' if cut['index']%2 else f'(iw-iw/zoom)*(1-{ratio})'
        graph.append(f'[0:v]zoompan=z=\'{zoom}\':x=\'{x}\':y=\'(ih-ih/zoom)/2\':d=1:s=1920x1080:fps=30,setsar=1[{node}]')
    else:graph.append(f'[0:v]format=rgba[{node}]')
    for i,layer in enumerate(cfg['layers'],1):
        start=layer['start'];end=layer['end'];label=f'l{i}';new=f'b{i}';img=f'[{i}:v]format=rgba'
        if layer.get('grow_seconds'):
            img+=',setpts=PTS-STARTPTS'
        else:img+=f',fade=t=in:st={start}:d=0.35:alpha=1'
        img+=f'[{label}]';graph.append(img)
        yy=str(layer['y']) if layer.get('grow_seconds') else f"{layer['y']}+28*(1-pow(clip((t-{start})/.5,0,1),.7))"
        graph.append(f"[{node}][{label}]overlay=x={layer['x']}:y='{yy}':enable='between(t,{start},{end})':shortest=0[{new}]");node=new
    if countfilters:
        new='num';graph.append(f'[{node}]'+','.join(countfilters)+f'[{new}]');node=new
    graph.append(f'[{node}]drawbox=x=0:y=920:w=1920:h=160:color=0x163544:t=fill,ass={folder}/captions.ass:fontsdir={FONTS}[cap]')
    graph.append(f'[cap][{len(cfg["layers"])+1}:v]overlay=0:0:shortest=0,format=yuv420p[v]')
    (folder/'filters.txt').write_text(';\n'.join(graph))
    args+=['-filter_complex_threads','2','-filter_complex_script',str(folder/'filters.txt'),'-map','[v]','-an','-frames:v',str(min(frames,120) if preview else frames),'-r','30','-c:v','libx264','-preset','veryfast','-crf','21','-threads','4','-movflags','+faststart',str(out)]
    run(args);save(marker,dict(inputs=fingerprint,frames=frames,sha256=sha(out),preview=preview))
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--sample',type=int,nargs='*');p.add_argument('--prepare-only',action='store_true');p.add_argument('--workers',type=int,default=3);args=p.parse_args();root=args.root
    version=int(root.name.rsplit('-v',1)[1])
    assert not (root.parents[1]/f'assets/promotion-film-v{version}.mp4').exists(),'Published version is immutable'
    script=json.loads((root/'script.json').read_text());voices=json.loads((root/'voice-manifest.json').read_text());olds=json.loads((root.parent/'promotion-v4/visual-plan.json').read_text());edits=editorial()
    assert len(olds)==114 and script['version']==9
    logo=ImageOps.contain(Image.open('/app/static/branding/category-v1/GumaStory.png').convert('RGBA'),(250,108))
    layer=Image.new('RGBA',(W,H));layer.alpha_composite(logo,(42,20));layer.save(root/'logo-layer.png')
    (root/'motion').mkdir(exist_ok=True);timeline=[];cues=[];cursor=0;chapters=[];tasks=[]
    for voice in voices:
        n=voice['index'];asr_path=root/'asr'/f'{n:03}.json'
        if not asr_path.exists():
            if args.sample:continue
            raise ValueError(f'ASR not ready: {n}')
        asr=json.loads(asr_path.read_text());assert asr['audio_sha256']==sha(root/'processed'/f'{n:03}.wav')
        duration=math.ceil((asr['duration']+.28)*FPS)/FPS+(2 if n==114 else 0)
        cut=dict(index=n,scene=voice['scene'],start=cursor,end=cursor+duration,speech_seconds=asr['duration'],duration=duration,text=voice['text'],processed_file=f'processed/{n:03}.wav',source_sha256=asr['source_sha256'])
        timeline.append(cut)
        if not chapters or chapters[-1]['scene']!=voice['scene']:chapters.append(dict(scene=voice['scene'],title=script['scenes'][voice['scene']-1]['title'],start=cursor))
        cursor+=duration
        if args.sample and n not in args.sample:continue
        folder,counts=prepare_cut(root,cut,voice,asr,olds[n-1],edits[n]);cues+=captions(root,cut,asr,edits[n])
        if not args.prepare_only:tasks.append((cut,folder,counts))
    if tasks:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures={pool.submit(encode_cut,root,c,folder,counts):c for c,folder,counts in tasks}
            for future in as_completed(futures):
                c=futures[future];future.result();print(json.dumps({'rendered':c['index'],'duration':c['duration'],'kind':olds[c['index']-1]['kind']}),flush=True)
    if args.sample:return
    assert len(timeline)==114
    for c,nxt in zip(chapters,chapters[1:]+[dict(start=cursor)]):c['end']=nxt['start']
    save(root/'timeline.json',dict(duration=cursor,paragraphs=timeline,chapters=chapters,tempo=1,caption_alignment='compact editorial cues mapped to ASR source sentences'))
    save(root/'caption-review.json',dict(font='Pretendard SemiBold',font_size=50.6,parent_font_size=46,increase_percent=10,cues=cues,full_narration_unchanged=True))
    save(root/'editorial.json',edits)
    vtt=['WEBVTT','']
    for cue in cues:vtt.extend([f'{vtt_time(cue["start"])} --> {vtt_time(cue["end"])}',cue['text'],''])
    (root/'captions.vtt').write_text('\n'.join(vtt))
    if args.prepare_only:return
    meta=[';FFMETADATA1','title='+script['title']]
    for c in chapters:meta+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["start"]*1000)}',f'END={round(c["end"]*1000)}','title='+c['title']]
    (root/'chapters.txt').write_text('\n'.join(meta))
    pcm=[]
    for cut in timeline:
        with wave.open(str(root/cut['processed_file']),'rb') as f:assert f.getframerate()==48000 and f.getnchannels()==1;data=f.readframes(f.getnframes())
        pcm.append(data+b'\0\0'*(round(cut['duration']*48000)-len(data)//2))
    with wave.open(str(root/'narration.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(b''.join(pcm))
    (root/'segments.txt').write_text('\n'.join(f"file '{root}/segments/{n:03}.mp4'" for n in range(1,115)))
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(root/'segments.txt'),'-i',str(root/'narration.wav'),'-i',str(root/'chapters.txt'),'-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-c:v','copy','-c:a','pcm_s16le','-t',str(cursor),str(root/'narrated.mkv')])
    print(json.dumps({'motion_complete':114,'duration':cursor,'captions':len(cues)}),flush=True)
if __name__=='__main__':main()
