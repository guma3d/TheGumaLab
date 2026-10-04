"""Astra-authored shopping cuts; local previews, selective Veo, private publication."""
import asyncio
import json
import re
import shutil
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator
DEFAULT_VOICE = "ko-KR-HyunsuMultilingualNeural"
from app.core import quality
from app.core import versions as store
from app.core import official_clips as media
from app.core.prepared_packages import digest, read, verify_package
from app.core.production_rules import snapshot
from app.core.recommendations import Recommendation, now_kst
from app.core.recommendations import validate_novelty
from app.core.categories import PRESETS
from app.core.tts_engine import synthesize_speech
from app.core.veo_client import generate_video_clip

ROLES = ('need', 'solution', 'reason', 'product', 'cta')


class Cut(BaseModel):
    role: Literal['need','solution','reason','product','cta']
    mode: Literal['official_clip','official_image','veo']
    source_file: str
    source_url: str
    evidence: str = Field(min_length=10)
    narration_ko: str = Field(min_length=1, max_length=250)
    hook: str = ''
    headline: str = Field(default='',max_length=32)
    covered_features: list[str] = Field(default_factory=list)
    start_seconds: float = Field(default=0, ge=0, allow_inf_nan=False)
    duration_seconds: float = Field(default=5, ge=2, le=6, allow_inf_nan=False)
    veo_prompt: str = ''
    preserve_actual: bool = False
    square_crop: bool = False

    @model_validator(mode='after')
    def validate_cut(self):
        from app.core.recommendations import Source
        Source.safe_url(self.source_url)
        if self.mode=='veo' and (len(self.veo_prompt.strip())<20 or self.preserve_actual):
            raise ValueError('Veo 컷에는 연출 프롬프트가 필요하며 실제 기술·음식 보존 컷은 생성하지 않습니다.')
        return self


class Board(BaseModel):
    author_model: Literal['gpt-6-astra']
    title: str = Field(min_length=1,max_length=100)
    summary: str
    popularity_basis: str = Field(min_length=10)
    popularity_claimed: bool = False
    popularity_source_url: str = ''
    cta_destination: Literal['channel_profile'] = 'channel_profile'
    scenes: list[Cut] = Field(min_length=6,max_length=8)

    @model_validator(mode='after')
    def funnel(self):
        roles=[s.role for s in self.scenes]
        if set(roles)!=set(ROLES) or roles!=sorted(roles,key=ROLES.index):
            raise ValueError('필요성 → 솔루션 → 관심 이유 → 제품 소개 → CTA 순서가 필요합니다.')
        if not self.scenes[0].hook.strip():raise ValueError('첫 컷 후킹 포인트가 필요합니다.')
        if self.popularity_claimed:
            from app.core.recommendations import Source
            Source.safe_url(self.popularity_source_url)
        elif any(word in s.narration_ko for s in self.scenes for word in ('인기','품절','판매 1위','판매량 1위','대세')):
            raise ValueError('인기 주장은 원문 근거가 필요합니다. 없으면 관심을 끄는 이유로 설명하세요.')
        if any(word in self.scenes[-1].narration_ko for word in ('하단 링크','댓글 링크','설명란 링크')):
            raise ValueError('쇼츠 CTA는 클릭 가능한 채널 프로필 링크로 안내하세요.')
        return self


def build(rec_path, board_path):
    """Input media must already be acquired and inspected by Codex; never fetch arbitrary URLs."""
    rec=Recommendation.model_validate(read(rec_path))
    if rec.category=='tech' and (not rec.purchase_link or rec.purchase_link.price_krw is None or rec.purchase_link.price_krw>500000 or len(rec.purchase_link.price_evidence)<10):
        raise ValueError('테크는 실제 확인한 50만원 이하 쿠팡 옵션 가격과 근거가 필요합니다.')
    validate_novelty(rec)
    if not rec.purchase_link or not rec.purchase_link.affiliate_url:
        raise ValueError('쿠팡 데이터와 실제 발급된 파트너스 링크를 먼저 확보하세요.')
    board=Board.model_validate(read(board_path))
    required={rec.key_feature,*rec.supporting_features[:2]}
    if not required <= {f for s in board.scenes for f in s.covered_features}:
        raise ValueError('핵심 기능과 추가 기능 설명이 누락됐습니다.')
    idea=store.create(rec.model_dump(mode='json'),now_kst().strftime('%Y-%m-%d'),approved=False)
    value,_=store.reserve(idea['id'],'Preview',True,execution_mode='astra_shopping')
    n=value['number'];folder=store.version_dir(idea['id'],'Preview',n)
    try:
        result=board.model_dump();result['pipeline']='shopping_v2';result['needs_3d']=False
        result['quality_revision']='director-v1'
        result['category_style']=dict(PRESETS[rec.category])
        store.write_json(folder/'recommendation.json',rec.model_dump(mode='json'))
        store.write_json(folder/'production_rules.json',snapshot(rec.category))
        for i,s in enumerate(board.scenes,1):
            source=Path(s.source_file).resolve()
            if not source.is_file() or source.suffix.lower() not in ('.mp4','.jpg','.jpeg','.png','.webp'):
                raise ValueError('직접 확인한 로컬 영상·이미지가 필요합니다.')
            copied=folder/f'source_{i:02d}{source.suffix.lower()}';shutil.copyfile(source,copied)
            measurement=quality.inspect_source(copied) if s.mode!='veo' else dict(context_reference_only=True)
            image=folder/f'scene_{i:02d}.png';clip=folder/f'scene_{i:02d}.mp4'
            if source.suffix.lower()=='.mp4':
                if s.start_seconds+s.duration_seconds>media.duration(source):raise ValueError('원본 범위 밖의 컷입니다.')
                framing=['-vf','crop=min(iw\\,ih):min(iw\\,ih)'] if s.square_crop else []
                media.run([media.get_ffmpeg_bin(),'-v','error','-ss',str(s.start_seconds),'-i',str(copied),'-t',str(s.duration_seconds),*framing,'-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(clip)])
                media.run([media.get_ffmpeg_bin(),'-v','error','-i',str(clip),'-frames:v','1',str(image)])
            else:
                from PIL import Image,ImageOps
                with Image.open(copied) as im:
                    rgba=ImageOps.exif_transpose(im).convert('RGBA')
                    # Palette transparency contains arbitrary RGB values; composite before dropping alpha.
                    background='#293638' if rec.category=='tech' else '#f5f5f5'
                    Image.alpha_composite(Image.new('RGBA',rgba.size,background),rgba).convert('RGB').save(image)
                from app.core.ffmpeg_mixer import render_product_still
                render_product_still(image,clip,'9:16',s.duration_seconds)
            media.sheets(clip,[0,s.duration_seconds*.5,s.duration_seconds-.12],folder,f'check_{i:02d}')
            result['scenes'][i-1].update(scene_number=i,visual_mode=s.mode,purpose=s.role,
                image_url=store.url(image),clip_url=store.url(clip),source_sha256=digest(copied),
                source_file=copied.name,enhance_3d=False)
            result['scenes'][i-1]['source_quality']=measurement
        store.write_json(folder/'storyboard.json',result)
        value=store.update(idea['id'],'Preview',n,status='awaiting_review',storyboard=result,needs_3d=False,
            message='Astra 컷씬 검수 대기',board_sha256=digest(folder/'storyboard.json'))
        return dict(value,idea_id=idea['id'])
    except Exception:
        store.update(idea['id'],'Preview',n,status='failed',message='컷씬 준비 실패 · 새 버전으로 재시도')
        raise


def seal(id,n,review_path):
    folder=store.version_dir(id,'Preview',n);v=store.get(id,'Preview',n);r=read(review_path)
    if v['status']!='awaiting_review':raise ValueError('검수 대기 버전만 확정할 수 있습니다.')
    if r.get('board_sha256')!=digest(folder/'storyboard.json') or r.get('reviewed_by')!='gpt-6-astra' or r.get('passed') is not True:
        raise ValueError('Astra의 실제 컷씬 검수와 일치하는 해시가 필요합니다.')
    checks=r.get('scenes',[])
    if len(checks)!=len(v['storyboard']['scenes']) or any(c.get('number')!=i or c.get('passed') is not True or not c.get('notes') for i,c in enumerate(checks,1)):
        raise ValueError('모든 컷의 실물·기능·후킹·원본 경계 검수가 필요합니다.')
    if v['storyboard'].get('quality_revision'):
        quality.validate_preflight(r)
    store.write_json(folder/'visual_review.json',r)
    files={p.relative_to(store.directory(id)).as_posix():digest(p) for p in folder.iterdir() if p.name!='version.json' and p.is_file()}
    store.write_json(folder/'package.json',dict(files=files,pipeline='shopping_v2',reviewed_by='gpt-6-astra',prepared_at=now_kst().isoformat()))
    return store.update(id,'Preview',n,status='ready',package_ready=True,message='컷씬 검수 완료 · 자동 영상 제작 준비')


def enqueue(id,n,regenerate=False,reuse_video_version=None):
    if store.read(id).get('archived'):
        raise ValueError('제외된 아이템은 새로 제작할 수 없습니다.')
    package=verify_package(id,n)
    if package.get('pipeline')!='shopping_v2':raise ValueError('새 쇼핑쇼츠 콘티로 준비해주세요.')
    folder=store.version_dir(id,'Preview',n);rec=read(folder/'recommendation.json')
    from app.core.recommendations import PurchaseLink
    purchase=PurchaseLink.model_validate(rec['purchase_link'])
    if rec['category']=='tech' and (purchase.price_krw is None or purchase.price_krw>500000 or len(purchase.price_evidence)<10):
        raise ValueError('테크는 확인된 50만원 이하 옵션만 제작합니다.')
    if not read(folder/'storyboard.json').get('quality_revision'):
        raise ValueError('새 해상도·감독 검수 기준으로 콘티를 다시 준비하세요.')
    previous=store.history(id,'Video')
    regenerate=regenerate or bool(previous and previous[0].get('preview_version')!=n)
    return store.reserve(id,'Video',regenerate,queued=True,preview_version=n,execution_mode='astra_shopping',
        storyboard=read(folder/'storyboard.json'),product_url=purchase.affiliate_url,voice=DEFAULT_VOICE,voice_rate='+15%',quality_revision='director-v1',reuse_video_version=reuse_video_version)[0]


async def render(id,n):
    v=store.get(id,'Video',n);verify_package(id,v['preview_version'])
    folder=store.version_dir(id,'Video',n);preview=store.version_dir(id,'Preview',v['preview_version'])
    board=v['storyboard'];segments=[];cut_outputs=[]
    # Validate every spoken duration before any paid Veo request.
    for i,scene in enumerate(board['scenes'],1):
        audio=folder/f'audio_{i:02d}.mp3'
        await synthesize_speech(scene['narration_ko'],audio,voice=v['voice'],rate=v.get('voice_rate','+15%'))
        if media.duration(audio)+.25>6.5:
            raise ValueError(f'CUT {i}: 대사를 6초 안팎으로 간결하게 수정하세요.')
    for i,scene in enumerate(board['scenes'],1):
        store.update(id,'Video',n,message=f'{i}/{len(board["scenes"])} 컷·고정 음성 제작')
        audio=folder/f'audio_{i:02d}.mp3'
        seconds=media.duration(audio)+.25
        if seconds>6.5:
            raise ValueError(f'CUT {i}: 대사가 {seconds:.1f}초입니다. 6초 안팎으로 간결하게 수정하세요.')
        raw=preview/f'scene_{i:02d}.mp4'
        if scene['mode']=='veo':
            raw=folder/f'veo_{i:02d}.mp4'
            reused=False
            if v.get('reuse_video_version'):
                parent=store.get(id,'Video',v['reuse_video_version'])
                old=parent['storyboard']['scenes'][i-1]
                source=store.version_dir(id,'Video',v['reuse_video_version'])/raw.name
                if source.is_file() and old.get('veo_prompt')==scene['veo_prompt'] and old.get('source_sha256')==scene.get('source_sha256'):
                    shutil.copyfile(source,raw);reused=True
            if not reused:
                await asyncio.to_thread(generate_video_clip,prompt=scene['veo_prompt']+' Full vertical composition, no letterboxing. No speech or subtitles. Contextual lifestyle illustration only; no identifiable product, brand, food close-up or engineering internals. Product and technology views use the original official media.',output_path=raw,duration_seconds=8,aspect_ratio='9:16',resolution='1080p')
            quality.inspect_source(raw)
        output=folder/f'cut_{i:02d}.mp4'
        style=board.get('category_style',PRESETS['tech'])
        subtitles=folder/f'captions_{i:02d}.ass'
        write_captions(subtitles,scene['narration_ko'],seconds,style,scene.get('headline',''),scene['mode']=='veo')
        # All runtime paths are controlled workspace paths; escape libavfilter delimiters.
        escaped=str(subtitles).replace('\\','/').replace(':',r'\:').replace("'",r"\'")
        framing=quality.generated_portrait_filter(raw) if scene['mode']=='veo' else quality.portrait_filter('293638' if style['label']=='신형 테크' else 'f4eee8')
        vf=framing+f",fps=30,tpad=stop_mode=clone:stop_duration={seconds},ass=filename='{escaped}'"
        await asyncio.to_thread(media.run,[media.get_ffmpeg_bin(),'-v','error','-i',str(raw),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-vf',vf,'-af','apad','-t',str(seconds),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',str(output)],240)
        segments.append(output)
        cut_quality=quality.inspect_output(output)
        cut_outputs.append(dict(number=i,role=scene["role"],narration_ko=scene["narration_ko"],video_url=store.url(output),audio_url=store.url(audio),mode=scene["mode"],technical_quality=cut_quality,file_sha256=digest(output)))
    listing=folder/'clips.txt';listing.write_text('\n'.join(f"file '{p.name}'" for p in segments),encoding='utf-8')
    output=folder/'final.mp4'
    await asyncio.to_thread(media.run,[media.get_ffmpeg_bin(),'-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(output)],240)
    technical=quality.inspect_output(output)
    store.write_json(folder/'technical_review.json',dict(technical,file_sha256=digest(output)))
    store.write_json(folder/'sources.json',dict(product_url=v['product_url'],scenes=board['scenes'],voice=v['voice']))
    store.write_json(folder/'upload.json',dict(state='quality_review',privacy='private',channel='https://www.youtube.com/@GumaShop86',
        title=board['title'],description=board['summary']+'\n상품은 채널 프로필 링크에서 확인하세요.\n'+v['product_url']+'\n쿠팡 파트너스 활동으로 일정액의 수수료를 제공받습니다.',file_sha256=digest(output)))
    return store.update(id,'Video',n,status='ready',cuts=cut_outputs,output_url=store.url(output),sources_url=store.url(folder/'sources.json'),message='영상 완성 · 음성·화면 검수 후 비공개 업로드',publication_state='quality_review')


def write_captions(path,text,seconds,style,headline='',generated=False):
    """Short readable subtitles in the same safe area for every category episode."""
    clean=re.sub(r'[{}\\\r\n]',' ',text)
    chunks=[];line=''
    for word in clean.split():
        # Korean words may be long; bound glyph count rather than trusting wrapping.
        for part in [word[i:i+18] for i in range(0,len(word),18)]:
            if line and len(line)+len(part)+1>18:chunks.append(line);line=''
            line=(line+' '+part).strip()
    if line:chunks.append(line)
    chunks=chunks or [' ']
    rgb=style['accent'];color='&H00'+rgb[4:6]+rgb[2:4]+rgb[:2]
    header=f'''[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{style['font']},38,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80101010,-1,0,0,0,100,100,0,0,1,3,1,2,55,100,240,1
Style: Brand,{style['font']},28,{color},{color},&H00101010,&H80101010,-1,0,0,0,100,100,0,0,1,2,0,7,48,100,150,1
Style: Headline,{style['font']},46,&H00FFFFFF,{color},&H00202020,&H00202020,-1,0,0,0,100,100,0,0,1,3,1,8,50,70,230,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    def clock(t):
        cs=round(t*100);return f'{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}'
    events=[f"Dialogue: 0,0:00:00.00,{clock(seconds)},Brand,,0,0,0,,GumaShop · {style['label']}"]
    if headline:
        title=re.sub(r'[{}\\\r\n]',' ',headline)
        events.append(f'Dialogue: 1,0:00:00.00,{clock(seconds)},Headline,,0,0,0,,{title}')
    if generated:
        events.append(f'Dialogue: 0,0:00:00.00,{clock(seconds)},Brand,,48,100,110,,AI 상황 연출')
    total=sum(map(len,chunks));elapsed=0
    for chunk in chunks:
        end=elapsed+seconds*len(chunk)/total
        events.append(f'Dialogue: 0,{clock(elapsed)},{clock(end)},Caption,,0,0,0,,{chunk}')
        elapsed=end
    path.write_text(header+'\n'.join(events)+'\n',encoding='utf-8')


def publication(id,n,action,evidence):
    """Records observed browser outcomes, never performs or pretends a YouTube upload."""
    if store.read(id).get('archived'):
        raise ValueError('제외된 아이템은 게시할 수 없습니다.')
    folder=store.version_dir(id,'Video',n);path=folder/'upload.json'
    with store.LOCK:
        data=read(path)
        if digest(folder/'final.mp4')!=data['file_sha256']:raise ValueError('검수 대상 영상이 변경됐습니다.')
        if len(evidence.get('notes',''))<10:raise ValueError('실제 확인 근거를 기록해주세요.')
        if action=='review':
            if store.get(id,'Video',n).get('quality_revision'):
                quality.validate_editorial(evidence)
                if evidence.get('file_sha256')!=data['file_sha256']:
                    raise ValueError('감독 검수 파일 해시가 현재 영상과 다릅니다.')
                technical=read(folder/'technical_review.json')
                if technical.get('file_sha256')!=data['file_sha256'] or technical.get('passed') is not True:
                    raise ValueError('최종 파일의 기술 검수가 필요합니다.')
            if data['state']!='quality_review' or evidence.get('audio_visual_passed') is not True:raise ValueError('실제 음성·화면 검수가 필요합니다.')
            data['state']='upload_pending'
        elif action=='claim':
            if data['state']!='upload_pending':raise ValueError('이미 진행 중입니다. Studio에서 기존 업로드를 먼저 확인하세요.')
            data['state']='uploading'
        elif action=='private':
            if data['state'] not in ('uploading','upload_pending'):raise ValueError('업로드 대기·진행 상태가 아닙니다.')
            if evidence.get('visibility')!='private' or evidence.get('channel')!=data['channel'] or not re.fullmatch(r'https://www.youtube.com/watch\?v=[A-Za-z0-9_-]{11}',evidence.get('url','')):
                raise ValueError('채널과 비공개 상태·영상 URL을 확인해주세요.')
            data.update(state='private',url=evidence['url'])
        elif action=='public':
            if data['state']!='publish_requested' or evidence.get('visibility')!='public' or evidence.get('url')!=data.get('url'):raise ValueError('사용자 공개 승인과 동일 영상 확인이 필요합니다.')
            data.update(state='public',privacy='public')
        else:raise ValueError('지원하지 않는 상태 변경입니다.')
        data.setdefault('events',[]).append(dict(action=action,at=now_kst().isoformat(),evidence=evidence))
        store.write_json(path,data)
        return store.update(id,'Video',n,publication_state=data['state'],youtube_url=data.get('url'),message={'private':'YouTube 비공개 · 사용자 최종 리뷰 대기','public':'YouTube 공개 완료'}.get(data['state'],'업로드 준비·검증 중'))
