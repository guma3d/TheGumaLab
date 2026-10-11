"""Compose clean v3 scenes, charts and thin numeric captions; no editorial overlays."""
import argparse, ast, hashlib, json, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from display_captions import display_text, assert_display_numbers
from clean_promotion_charts import compose as clean_charts

def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('--render',action='store_true');args=parser.parse_args()
    root=args.root.resolve(); parent=root.parent/'promotion-v2'
    if (root.parents[1]/'imports/promotion-film-v3.json').exists():
        raise SystemExit('Published v3 is immutable. Prepare a new version for further changes.')
    base=Path('/app') if Path('/app/app/assets/fonts').exists() else Path(__file__).resolve().parents[2]
    fonts=base/'app/assets/fonts';assets=root.parents[1]/'assets'
    timeline=json.loads((root/'timeline.json').read_text(encoding='utf-8'))
    visual=json.loads((parent/'visual-plan.json').read_text(encoding='utf-8'))
    jobs=json.loads((root/'image-jobs.json').read_text(encoding='utf-8'))
    # Read data tables from legacy compositor without executing the legacy reference-reuse path.
    tree=ast.parse((Path(__file__).parent/'compose_longform.py').read_text(encoding='utf-8'))
    data={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('cards','tables') for t in node.targets):
            data[node.targets[0].id]=ast.literal_eval(node.value)
    def ft(size):return ImageFont.truetype(str(fonts/'Pretendard-SemiBold.otf'),size)
    W,H=1920,1080;cream='#F6F0E4';navy='#183444';teal='#267C7B'
    def lines(value,width,size):
        result=[];line='';measure=ImageDraw.Draw(Image.new('RGB',(1,1)))
        for word in value.split():
            trial=(line+' '+word).strip()
            if line and measure.textlength(trial,font=ft(size))>width:result.append(line);line=word
            else:line=trial
        if line:result.append(line)
        return result
    def put(draw,pos,value,size=48,width=1700,color=navy):
        visible.append(value)
        x,y=pos
        for line in lines(value,width,size):draw.text((x,y),line,font=ft(size),fill=color);y+=size*1.28
        return y
    clean_charts(root,fonts)
    replacements={'가상 업무 상황':'직함은 바뀌었는데, 결정권은?', '가상의 두 팀':'서로 다른 두 팀', '편집자 제안 · 성장의 경로':'성장의 두 가지 경로', '가상 일정 · 관리 뒤에 남은 실무':'퇴근할 때 시작되는 실무', '가상 제안 A':'제안 A', '가상 제안 B':'제안 B'}
    def clean_title(title): return replacements.get(title,title)
    output=root/'frames';output.mkdir(exist_ok=True)
    reference_hashes={sha(assets/(rid+'.png')) for j in jobs for rid in j['reference_ids']}
    image_hashes=[];plan=[]
    for old in visual:
        n=old['index'];key=(old['scene'],old['paragraph']);visible=[]
        im=Image.new('RGB',(W,H),cream);d=ImageDraw.Draw(im)
        if 'illustration' in old['kind']:
            path=root/f'images/{n:03}.png'
            if not path.exists():raise FileNotFoundError(f'New scene image required: {path}')
            image_hash=sha(path)
            assert image_hash not in reference_hashes,'Reference portrait cannot be final footage'
            assert image_hash not in image_hashes,'Repeated illustration is not a new scene'
            image_hashes.append(image_hash)
            im=ImageOps.fit(Image.open(path).convert('RGB'),(W,H),Image.Resampling.LANCZOS)
            # Gradients are compositing for caption contrast, never used as image substitutes.
            overlay=Image.new('RGBA',(W,H));g=ImageDraw.Draw(overlay)
            for y in range(840,1080):g.line((0,y,W,y),fill=(10,21,30,round(190*(y-840)/239)))
            for y in range(135):g.line((0,y,W,y),fill=(10,21,30,round(95*(1-y/135))))
            im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB');d=ImageDraw.Draw(im)
            image_id=f'promotion-v2-scene-{n:03}'
        elif old['kind']=='chart':
            # Exact sourced chart images, no ImageGen numerals.
            p=Image.open(root/f'charts/{int(old["image_id"][-2:]):02}.png').convert('RGB')
            im.paste(p,(0,0));d=ImageDraw.Draw(im);image_id=f'promotion-v3-chart-{int(old["image_id"][-2:]):02}'
            visible.extend(json.loads((root/'chart-provenance.json').read_text(encoding='utf-8'))[int(old['image_id'][-2:])-1]['visible_labels'])
        elif key in data['cards']:
            title,points=data['cards'][key];put(d,(110,190),clean_title(title),72,1680)
            gap=28;cw=(1700-gap*(len(points)-1))//len(points)
            for k,point in enumerate(points):
                x=110+k*(cw+gap);d.rounded_rectangle((x,370,x+cw,790),28,fill='white')
                d.rounded_rectangle((x,370,x+cw,381),6,fill=teal if k%2==0 else '#C69227')
                put(d,(x+34,518),point,52 if len(points)<3 else 46,cw-68)
            image_id=''
        else:
            title,rows=data['tables'][key];put(d,(110,155),clean_title(title),64,1680)
            for k,row in enumerate([('질문','확인할 내용')]+rows):
                y=300+k*103;d.rounded_rectangle((110,y,1810,y+94),12,fill=teal if k==0 else 'white')
                color='white' if k==0 else navy
                put(d,(140,y+24),row[0],34,650,color);put(d,(835,y+24),row[1],34,940,color)
            image_id=''
        if 'illustration' not in old['kind']:
            # Dark caption zone makes a thin single stroke readable over light charts.
            d.rectangle((0,934,W,H),fill=navy)
        # Production labels and citations are retained in web provenance, never burned in.
        assert not any(word in text for word in ('가상','설명용','편집자','/ 12','V4') for text in visible)
        file=output/f'{n:03}.png';im.save(file)
        plan.append(dict(old,text=timeline['paragraphs'][n-1]['text'],image_id=image_id,file=f'frames/{n:03}.png',frame_sha256=sha(file),visible_text=visible,reused_scene_from_v2=('illustration' in old['kind']),generated=False))
    assert len(image_hashes)==65
    (root/'visual-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')

    def at(t):
        cs=round(t*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
    def vt(t):
        ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
    captions=[];events=[];vtt=['WEBVTT',''];changes=[]
    for p in timeline['paragraphs']:
        value=display_text(p['text']);assert_display_numbers(value)
        if value!=p['text']:changes.append(dict(index=p['index'],spoken=p['text'],display=value))
        chunks=lines(value,1510,46)
        groups=['\n'.join(chunks[i:i+2]) for i in range(0,len(chunks),2)]
        weights=[len(re.sub(r'\s','',g)) for g in groups];t=p['start']+.03
        for g,weight in zip(groups,weights):
            end=min(p['start']+p['speech_seconds'],t+p['speech_seconds']*weight/sum(weights))
            safe=g.replace('{','').replace('}','').replace('\n',r'\N')
            events.append(f'Dialogue: 0,{at(t)},{at(end)},Caption,,0,0,0,,{safe}')
            vtt.extend([f'{vt(t)} --> {vt(end)}',g,'']);captions.append(dict(index=p['index'],start=t,end=end,text=g));t=end
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Pretendard SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H00201912,&H70000000,0,0,0,0,100,100,0,0,1,1.3,0.4,2,120,120,48,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    (root/'captions.ass').write_text(header+'\n'.join(events)+'\n',encoding='utf-8')
    (root/'captions.vtt').write_text('\n'.join(vtt),encoding='utf-8')
    (root/'caption-review.json').write_text(json.dumps(dict(style='Pretendard SemiBold 46px, normal flag, single 1.3px outline, no pop',changes=changes,cues=captions),ensure_ascii=False,indent=2),encoding='utf-8')
    logo=Image.open(base/'static/branding/category-v1/GumaStory.png').convert('RGBA')
    logo=ImageOps.contain(logo,(250,108),Image.Resampling.LANCZOS)
    layer=Image.new('RGBA',(W,H));layer.alpha_composite(logo,(42,20));layer.save(root/'logo-layer.png')
    # All compositions + final-layer logo, subtitles inspected on encoded review sheets later.
    for page in range(6):
        sheet=Image.new('RGB',(1920,1000),cream);sd=ImageDraw.Draw(sheet)
        for k,p in enumerate(plan[page*20:(page+1)*20]):
            frame=Image.open(root/p['file']).convert('RGBA');frame.alpha_composite(layer)
            x=k%5*384;y=k//5*250;sheet.paste(frame.convert('RGB').resize((384,216)),(x,y));sd.text((x+6,y+219),f'{p["index"]:03}',font=ft(20),fill=navy)
        sheet.save(root/f'contact-{page+1:02}.jpg',quality=90)
    print(json.dumps({'reused_scene_images':len(image_hashes),'frames':len(plan),'caption_changes':len(changes)}),flush=True)
    if args.render: raise SystemExit('Use render_promotion_v3.py after the voice timeline is ready.')

if __name__=='__main__':main()
