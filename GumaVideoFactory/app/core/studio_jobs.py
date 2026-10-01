"""Version-scoped jobs. Nothing downstream starts until its parent is approved."""
import asyncio
import json
import logging
import shutil
import subprocess
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from app.config import DEFAULT_VOICE
from app.core import versions as store
from app.core import blender_runner as blender
from app.core.model_assets import discover, reconstruct, fetch
from app.core.categories import PRESETS
from app.core.planner import plan_video_storyboard
from app.core.image_client import generate_preview_image
from app.core.veo_client import generate_video_clip
from app.core.source_media import MediaSource, download_media, download_youtube_cc, media_preview, render_source_clip
from app.core.tts_engine import synthesize_speech
from app.core.ffmpeg_mixer import get_ffmpeg_bin

logger = logging.getLogger(__name__)


def progress(idea_id, stage, number, text):
    store.update(idea_id, stage, number, message=text)


async def execute(idea_id, stage, number):
    try:
        if stage == '3DModel': await asyncio.to_thread(model_job, idea_id, number)
        elif stage == 'Preview': await asyncio.to_thread(preview_job, idea_id, number)
        else: await video_job(idea_id, number)
    except Exception as error:
        logger.exception('Studio job failed: %s %s v%s', idea_id, stage, number)
        # Provider exceptions may contain request URLs. Keep credentials out of UI.
        safe = str(error) if isinstance(error, ValueError) else '제작 중 오류가 발생했습니다. 서버 로그를 확인한 뒤 재생성해주세요.'
        store.update(idea_id, stage, number, status='failed', message=safe[:600])


def model_job(idea_id, number):
    if store.get(idea_id,'3DModel',number).get('revision_operation'):
        return model_revision_job(idea_id,number)
    idea=store.read(idea_id); rec=idea['recommendation']; folder=store.version_dir(idea_id,'3DModel',number)
    report=lambda text: progress(idea_id,'3DModel',number,text)
    if idea['category']=='food':
        report('추천에 연결된 실사 자료를 확보합니다.')
        sources=[]
        for candidate in rec.get('media_sources',[]):
            source=MediaSource(**candidate)
            if not source.local_file:
                source.local_file=download_youtube_cc(source) if source.provider=='youtube_cc' else download_media(source)
            target=folder / (f'asset_{len(sources)+1:02d}' + source.file_path().suffix)
            shutil.copyfile(source.file_path(), target)
            preview=folder / f'view_{len(sources)+1}.png'; media_preview(source,preview,'9:16')
            sources.append(dict(source.model_dump(), snapshot_file=target.name, preview_url=store.url(preview)))
        uploaded=store.directory(idea_id)/'inputs'/'food.json'
        if uploaded.exists():
            for candidate in json.loads(uploaded.read_text(encoding='utf-8')):
                source=MediaSource(**candidate); target=folder / (f'asset_{len(sources)+1:02d}'+source.file_path().suffix)
                shutil.copyfile(source.file_path(),target)
                preview=folder/f'view_{len(sources)+1}.png';media_preview(source,preview,'9:16')
                sources.append(dict(source.model_dump(),snapshot_file=target.name,preview_url=store.url(preview)))
        store.write_json(folder/'sources.json',sources)
        if not sources: raise ValueError('실사 자료가 아직 없습니다. 출처와 사용 조건을 함께 등록한 뒤 재생성해주세요.')
        store.update(idea_id,'3DModel',number,status='ready',kind='real_media',sources=sources,
                     images=[s['preview_url'] for s in sources],message='실사 자료를 확인하고 승인해주세요.')
        return
    inputs=store.directory(idea_id)/'inputs'
    try:
        sources=discover(rec,folder,report)
    except Exception:
        if not list(inputs.glob('reference_*.jpg')):raise
        sources=dict(references=[],models=[],search_note='검색에 실패해 등록한 제품 사진으로 진행했습니다.')
    for path in sorted(inputs.glob('reference_*.jpg'))[-6:]:
        target=folder/('user_'+path.name);shutil.copyfile(path,target)
        sources['references'].insert(0,dict(file=target.name,url='',page_url='',description='사용자 제품 참고 사진',usage='모델링 참고용'))
    store.write_json(folder/'sources.json',sources)
    refs=[dict(s,preview_url=store.url(folder/s['file'])) for s in sources['references']]
    store.update(idea_id,'3DModel',number,references=refs,candidates=sources.get('models',[]),sources_url=store.url(folder/'sources.json'))
    if not refs: raise ValueError('제품 사진을 확보하지 못했습니다. 참고 사진을 등록하고 재생성해주세요.')
    imported=None; selected=None
    for candidate_index,candidate in enumerate(sources.get('models',[])[:8],1):
        # Private inspection of a public download is not publication approval.
        # Usage rights must be confirmed in the explicit model approval gate.
        if not candidate.get('download_url'): continue
        suffix=Path(urlparse(candidate.get('download_url','')).path).suffix.lower()
        if suffix not in ('.blend','.glb','.usdz','.obj','.fbx'): continue
        try:
            report('공개 모델을 내려받아 형상을 확인합니다.')
            imported=folder/('downloaded'+suffix); imported.write_bytes(fetch(candidate['download_url'],150*1024*1024))
            attempt=folder/f'attempt_{candidate_index:02d}';attempt.mkdir(exist_ok=False)
            blender.build(attempt,imported,rec['subject'])
            for name in ['model.blend','inspection.json']+[f'view_{i}.png' for i in range(1,5)]:
                shutil.copyfile(attempt/name,folder/name)
            selected=candidate;break
        except Exception:
            imported=None
            logger.info('Model candidate unavailable for %s',idea_id)
    uncertainties=[]
    if not imported:
        report('제품 사진을 분석해 편집 가능한 3D 초안을 만듭니다.')
        blueprint=reconstruct(rec,sources,folder);uncertainties=blueprint.uncertainties
        report('Blender에서 제품의 네 방향 프리뷰를 렌더링합니다.')
        blender.build(folder,product_name=rec['subject'])
    inspection=json.loads((folder/'inspection.json').read_text(encoding='utf-8'))
    store.update(idea_id,'3DModel',number,status='ready',kind='downloaded' if imported else 'reconstructed',
        selected_source=selected,uncertainties=uncertainties,inspection=inspection,
        images=[store.url(folder/f'view_{i}.png') for i in range(1,5)],model_url=store.url(folder/'model.blend'),
        message='외형 검토가 필요합니다. 사진과 모델의 형태·카메라·버튼·색상을 비교하고 승인해주세요.')


def model_revision_job(idea_id,number):
    """Reimport the existing source into a NEW version without paid research."""
    version=store.get(idea_id,'3DModel',number)
    if version['revision_operation']!='single_product':raise ValueError('지원하지 않는 모델 수정입니다.')
    parent=store.get(idea_id,'3DModel',version['parent_model_version'])
    original=store.version_dir(idea_id,'3DModel',parent['number'])
    folder=store.version_dir(idea_id,'3DModel',number)
    source=next((p for p in original.glob('downloaded.*') if p.suffix in ('.usdz','.glb','.blend','.obj','.fbx')),None)
    if source is None:raise ValueError('수정에 필요한 원본 3D 자료가 없습니다.')
    source_copy=folder/source.name;shutil.copyfile(source,source_copy)
    refs=[]
    for ref in parent.get('references',[]):
        filename=Path(ref['file']).name
        shutil.copyfile(original/filename,folder/filename)
        refs.append(dict(ref,preview_url=store.url(folder/filename)))
    for name in ('sources.json','search.json'):
        if (original/name).is_file():shutil.copyfile(original/name,folder/name)
    progress(idea_id,'3DModel',number,'원본에서 정확한 기종 한 대를 분리해 새 버전으로 렌더링합니다.')
    blender.build(folder,source_copy,store.read(idea_id)['recommendation']['subject'])
    inspection=json.loads((folder/'inspection.json').read_text(encoding='utf-8'))
    if inspection.get('selected_product_count')!=1 or inspection.get('selection')!='verified_dimensions':
        raise ValueError('원본에서 정확한 단일 제품을 분리하지 못했습니다. 기존 버전은 보존됩니다.')
    store.update(idea_id,'3DModel',number,status='ready',kind='downloaded',references=refs,
        candidates=parent.get('candidates',[]),selected_source=parent.get('selected_source'),
        sources_url=store.url(folder/'sources.json'),inspection=inspection,
        parent_model_sha256=hashlib.sha256((original/'model.blend').read_bytes()).hexdigest(),
        source_asset_sha256=hashlib.sha256(source_copy.read_bytes()).hexdigest(),
        images=[store.url(folder/f'view_{i}.png') for i in range(1,5)],model_url=store.url(folder/'model.blend'),
        message='제품 한 대로 수정했습니다. 이전 버전은 보존되어 있습니다. 외형을 확인하고 이 버전을 승인해주세요.')


def preview_job(idea_id, number):
    idea=store.read(idea_id); rec=idea['recommendation']; version=store.get(idea_id,'Preview',number)
    folder=store.version_dir(idea_id,'Preview',number); model_folder=store.version_dir(idea_id,'3DModel',version['model_version'])
    model=store.get(idea_id,'3DModel',version['model_version'])
    report=lambda text:progress(idea_id,'Preview',number,text)
    report('승인한 자료를 기준으로 6컷 대본을 기획합니다.')
    board=plan_video_storyboard(user_idea=rec['hook'],target_duration=24,scene_count=6,
        category=idea['category'],style_prompt=PRESETS[idea['category']]['style'],
        evidence=json.dumps(rec,ensure_ascii=False),approved_model=idea['category']=='tech').model_dump()
    store.write_json(folder/'storyboard.json',board)
    for idx,scene in enumerate(board['scenes']):
        report(f'{idx+1}/6 컷 프리뷰를 렌더링합니다.')
        path=folder/f'scene_{idx+1:02d}.png'
        if idea['category']=='food':
            sources=model['sources']; candidate=sources[min(idx,len(sources)-1)]
            source=MediaSource(**candidate)
            media_preview(source,path,'9:16')
            scene.update(visual_mode='real_media',media_source=candidate)
        elif idx in (1,2):
            generate_preview_image(scene['visual_prompt']+' Only isolated conceptual mechanisms. No complete product or exterior. No invented internal layout.',
                path,'9:16',PRESETS['tech']['style'])
            scene['visual_mode']='mechanism_concept'
        else:
            angle=[25,0,0,145,315,20][idx]
            blender.still(model_folder/'model.blend',path,angle)
            scene.update(visual_mode='approved_model',camera_angle=angle)
        scene['image_url']=store.url(path)
        store.write_json(folder/'storyboard.json',board)
    store.update(idea_id,'Preview',number,status='ready',storyboard=board,
        message='컷과 대본을 확인하고 최종 승인 후 영상을 제작해주세요.')


async def video_job(idea_id, number):
    idea=store.read(idea_id); version=store.get(idea_id,'Video',number)
    folder=store.version_dir(idea_id,'Video',number)
    preview=store.get(idea_id,'Preview',version['preview_version'])
    preview_folder=store.version_dir(idea_id,'Preview',version['preview_version'])
    model_folder=store.version_dir(idea_id,'3DModel',preview['model_version'])
    board=version['storyboard']; store.write_json(folder/'approved_storyboard.json',board)
    width,height=blender.video_size()
    clips=[]
    for idx,scene in enumerate(board['scenes'],1):
        progress(idea_id,'Video',number,f'{idx}/6 컷 영상·음성을 만듭니다.')
        audio=folder/f'audio_{idx:02d}.mp3'
        await synthesize_speech(scene['narration_ko'],audio,voice=DEFAULT_VOICE)
        result=await asyncio.to_thread(subprocess.run,['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(audio)],capture_output=True,text=True,timeout=30)
        duration=max(4,float(result.stdout.strip())+.3)
        raw=folder/f'raw_{idx:02d}.mp4'
        if scene['visual_mode']=='approved_model':
            await asyncio.to_thread(blender.clip,model_folder/'model.blend',raw,scene['camera_angle'],duration)
        elif scene['visual_mode']=='real_media':
            await asyncio.to_thread(render_source_clip,MediaSource(**scene['media_source']),raw,'9:16',4)
        else:
            await asyncio.to_thread(generate_video_clip,prompt=scene['visual_prompt']+' Animate only the isolated concept. No complete product or exterior.',
                output_path=raw,duration_seconds=4,aspect_ratio='9:16',image_path=preview_folder/f'scene_{idx:02d}.png')
        output=folder/f'clip_{idx:02d}.mp4'
        cmd=[get_ffmpeg_bin(),'-v','error','-i',str(raw),'-i',str(audio),'-map','0:v:0','-map','1:a:0',
            '-vf',f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,tpad=stop_mode=clone:stop_duration={duration}',
            '-af','apad','-t',str(duration),'-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2',str(output)]
        mux=await asyncio.to_thread(subprocess.run,cmd,capture_output=True,timeout=240)
        if mux.returncode: raise ValueError('음성·영상 합성에 실패했습니다.')
        clips.append(output)
    listing=folder/'clips.txt';listing.write_text('\n'.join(f"file '{p.name}'" for p in clips),encoding='utf-8')
    output=folder/'final.mp4'
    joined=await asyncio.to_thread(subprocess.run,[get_ffmpeg_bin(),'-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(output)],capture_output=True,timeout=180)
    if joined.returncode: raise ValueError('최종 영상 합성에 실패했습니다.')
    model=store.get(idea_id,'3DModel',preview['model_version'])
    credits=folder/'sources.json';store.write_json(credits,dict(product_url=version['product_url'],model_source=model.get('selected_source'),media=model.get('sources',[]),research=idea['recommendation']['sources']))
    store.update(idea_id,'Video',number,status='ready',output_url=store.url(output),sources_url=store.url(credits),message='영상이 완성됐습니다.')
