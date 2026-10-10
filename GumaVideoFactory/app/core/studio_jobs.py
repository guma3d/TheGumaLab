"""Version-scoped jobs. Nothing downstream starts until its parent is approved."""
import asyncio
import copy
import json
import logging
import shutil
import subprocess
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from app.config import DEFAULT_VOICE
from app.core import versions as store
from app.core.production_rules import snapshot as rules_snapshot, prompt_context
from app.core import blender_runner as blender
from app.core.model_assets import discover, reconstruct, fetch
from app.core.categories import PRESETS
from app.core.planner import plan_video_storyboard
from app.core.scene_visuals import validate_tech_visuals
from app.core.feature_references import resolve_feature_references, motion_prompt, review_feature_image, apply_reference_policy
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
        rules=rules_snapshot(store.read(idea_id)['category'])
        store.write_json(store.version_dir(idea_id,stage,number)/'production_rules.json',rules)
        store.update(idea_id,stage,number,production_rules_revision=rules['revision'],production_rules_sha256=rules['sha256'])
        if stage == '3DModel': raise ValueError('3D 모델 기능은 제거되었습니다.')
        elif stage == 'Preview': raise ValueError('컷씬은 현재 세션이 shopping_package.py로 준비합니다.')
        else: await video_job(idea_id, number)
    except Exception as error:
        logger.exception('Studio job failed: %s %s v%s', idea_id, stage, number)
        # Provider exceptions may contain request URLs. Keep credentials out of UI.
        safe = str(error) if isinstance(error, ValueError) else '제작 중 오류가 발생했습니다. 서버 로그를 확인한 뒤 재생성해주세요.'
        store.update(idea_id, stage, number, status='failed', message=safe[:600])


def model_job(idea_id, number):
    if store.read(idea_id)['category']=='tech':
        raise ValueError('테크 사전 준비는 Codex 예약 작업에서 로컬 도구로 처리합니다.')
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
    if version['revision_operation'] not in ('single_product','restore_materials'):raise ValueError('지원하지 않는 모델 수정입니다.')
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
    progress(idea_id,'3DModel',number,'원본의 제품 구성과 표면 재질을 새 버전으로 렌더링합니다.')
    blender.build(folder,source_copy,store.read(idea_id)['recommendation']['subject'])
    inspection=json.loads((folder/'inspection.json').read_text(encoding='utf-8'))
    if version['revision_operation']=='single_product' and (inspection.get('selected_product_count')!=1 or inspection.get('selection')!='verified_dimensions'):
        raise ValueError('원본에서 정확한 단일 제품을 분리하지 못했습니다. 기존 버전은 보존됩니다.')
    if version['revision_operation']=='restore_materials' and inspection.get('selected_product_count')!=parent.get('inspection',{}).get('selected_product_count'):
        raise ValueError('재질 수정 중 제품 구성이 달라져 완료하지 않았습니다.')
    store.update(idea_id,'3DModel',number,status='ready',kind='downloaded',references=refs,
        candidates=parent.get('candidates',[]),selected_source=parent.get('selected_source'),
        sources_url=store.url(folder/'sources.json'),inspection=inspection,
        parent_model_sha256=hashlib.sha256((original/'model.blend').read_bytes()).hexdigest(),
        source_asset_sha256=hashlib.sha256(source_copy.read_bytes()).hexdigest(),
        images=[store.url(folder/f'view_{i}.png') for i in range(1,5)],model_url=store.url(folder/'model.blend'),
        message='새 모델 버전이 완성됐습니다. 이전 버전은 보존되어 있습니다. 외형을 확인하고 이 버전을 승인해주세요.')


def preview_job(idea_id, number):
    if store.read(idea_id)['category']=='tech':
        raise ValueError('테크 프리뷰는 Codex 예약 작업에서 준비합니다. 유료 분석은 호출하지 않습니다.')
    if store.read(idea_id)['category']=='tech' and not store.get(idea_id,'Preview',number).get('model_version'):
        from app.core.official_clips import create_preview
        return create_preview(idea_id,number,lambda text:progress(idea_id,'Preview',number,text))
    idea=store.read(idea_id); rec=idea['recommendation']; version=store.get(idea_id,'Preview',number)
    folder=store.version_dir(idea_id,'Preview',number); model_folder=store.version_dir(idea_id,'3DModel',version['model_version'])
    model=store.get(idea_id,'3DModel',version['model_version'])
    report=lambda text:progress(idea_id,'Preview',number,text)
    report('승인한 자료를 기준으로 6컷 대본을 기획합니다.')
    parent_folder=None
    revisions=version.get('scene_revisions')
    if revisions:
        parent=store.get(idea_id,'Preview',version['parent_preview_version'])
        if parent['status']!='ready' or parent['model_version']!=version['model_version']:
            raise ValueError('같은 모델을 사용하는 완성 프리뷰에서 수정해주세요.')
        parent_folder=store.version_dir(idea_id,'Preview',parent['number'])
        board=copy.deepcopy(parent['storyboard'])
        for key,changes in revisions.items():
            index=int(key)-1
            if not 0<=index<len(board['scenes']):raise ValueError('수정할 컷 번호를 확인해주세요.')
            if set(changes)-{'visual_mode','visual_subject','visual_prompt','narration_ko','purpose','covered_features','camera_movement','reference_candidates','reference_limitation','reference_presentation','camera_angle','camera_settings'}:
                raise ValueError('지원하지 않는 컷 수정 항목입니다.')
            if changes.get('visual_mode',board['scenes'][index].get('visual_mode'))=='approved_model':
                for name in ('reference_presentation','reference_scene_file','reference_camera_distance','visual_review'):
                    board['scenes'][index].pop(name,None)
            board['scenes'][index].update(changes)
        # Older saved previews did not have the descriptive subject field.
        for scene in board['scenes']:
            scene.setdefault('visual_subject',scene.get('purpose','제품 설명'))
    else:
        board=plan_video_storyboard(user_idea=rec['hook'],target_duration=24,scene_count=6,
            category=idea['category'],style_prompt=PRESETS[idea['category']]['style']+prompt_context(idea['category']),
            evidence=json.dumps(rec,ensure_ascii=False),approved_model=idea['category']=='tech').model_dump()
    if idea['category']=='tech':validate_tech_visuals(board['scenes'])
    store.write_json(folder/'storyboard.json',board)
    for idx,scene in enumerate(board['scenes']):
        report(f'{idx+1}/6 컷 프리뷰를 렌더링합니다.')
        path=folder/f'scene_{idx+1:02d}.png'
        metadata_only=(parent_folder and str(idx+1) in revisions and
            set(revisions[str(idx+1)])<={'reference_limitation','camera_movement','purpose'})
        if parent_folder and (str(idx+1) not in revisions or metadata_only):
            shutil.copyfile(parent_folder/f'scene_{idx+1:02d}.png',path)
            attachments=[r['file'] for r in scene.get('feature_references',[])]
            if scene.get('reference_scene_file'):attachments.append(scene['reference_scene_file'])
            for name in attachments:
                if Path(name).name!=name:raise ValueError('잘못된 참고자료 파일 이름입니다.')
                shutil.copyfile(parent_folder/name,folder/name)
            for ref in scene.get('feature_references',[]):ref['preview_url']=store.url(folder/ref['file'])
        elif idea['category']=='food':
            sources=model['sources']; candidate=sources[min(idx,len(sources)-1)]
            source=MediaSource(**candidate)
            media_preview(source,path,'9:16')
            scene.update(visual_mode='real_media',media_source=candidate)
        elif scene['visual_mode']=='mechanism_concept':
            report(f'{idx+1}/{len(board["scenes"])} 컷의 기능별 공식 참고 이미지를 확인합니다.')
            refs=resolve_feature_references(rec['subject'],scene,folder,scene.get('reference_candidates'))
            scene['feature_references']=refs
            scene['reference_limitation']=' · '.join(r.get('limitation','') for r in refs if r.get('limitation'))
            apply_reference_policy(scene,refs)
            if scene.get('reference_presentation'):
                # Exact published pixels take priority over a distorted AI reconstruction.
                kind='thermal' if scene['reference_presentation']=='abstract_thermal' else 'display'
                blender.reference_still(folder/refs[0]['file'],path,scene.get('camera_angle',25),kind=kind)
                scene['reference_limitation']+=(' · 물리 원리의 추상 3D 연출입니다. 실제 챔버 형상을 재현하지 않습니다.' if kind=='thermal'
                    else ' · 공식 이미지 원본을 보존한 3D 디스플레이 연출이며 부품 복원 모델이 아닙니다.')
                scene['visual_review']=dict(passed=True,method='abstract_physics_not_product_geometry' if kind=='thermal' else 'unmodified_official_texture',reference_sha256=refs[0]['sha256'])
                scene['reference_scene_file']=path.with_suffix('.blend').name
                scene['reference_camera_distance']=4.3 if kind=='thermal' else 5.8
            else:
                generate_preview_image(motion_prompt(scene),path,'9:16',PRESETS['tech']['style'],
                    product_name=rec['subject'],feature_references=[dict(path=folder/r['file'],context=json.dumps(r,ensure_ascii=False)) for r in refs])
                scene['visual_review']=review_feature_image(scene,path,refs,folder)
            scene['visual_mode']='mechanism_concept'
        else:
            if parent_folder:
                for ref in scene.get('feature_references',[]):
                    shutil.copyfile(parent_folder/ref['file'],folder/ref['file'])
                    ref['preview_url']=store.url(folder/ref['file'])
            angle=(scene.get('camera_settings') or {}).get('start_angle',scene.get('camera_angle',[25,70,110,145,315,20,225,25][idx]))
            if scene.get('camera_settings'):
                blender.still(model_folder/'model.blend',path,angle,camera_settings=scene['camera_settings'])
            else:blender.still(model_folder/'model.blend',path,angle)
            scene.update(visual_mode='approved_model',camera_angle=angle)
        scene['image_url']=store.url(path)
        store.write_json(folder/'storyboard.json',board)
    store.update(idea_id,'Preview',number,status='ready',storyboard=board,
        message='컷과 대본을 확인하고 최종 승인 후 영상을 제작해주세요.')


async def video_job(idea_id, number):
    idea=store.read(idea_id); version=store.get(idea_id,'Video',number)
    if version.get('execution_mode') in ('session_shopping','astra_shopping'):
        from app.core.shopping import render
        return await render(idea_id,number)
    if idea['category']=='tech':
        raise ValueError('테크는 imagegen 고정 카메라 콘티를 shopping_package.py로 새로 준비하세요. 기존 3D·Veo 제작 경로는 사용하지 않습니다.')
    folder=store.version_dir(idea_id,'Video',number)
    preview=store.get(idea_id,'Preview',version['preview_version'])
    preview_folder=store.version_dir(idea_id,'Preview',version['preview_version'])
    model_number=version.get('model_version') or preview.get('model_version')
    model_folder=store.version_dir(idea_id,'3DModel',model_number) if model_number else None
    board=version['storyboard']; store.write_json(folder/'approved_storyboard.json',board)
    width,height=blender.video_size()
    clips=[]
    if idea['category']=='tech' and version.get('veo_transition'):
        from app.core.prepared_packages import verify_package
        verify_package(idea_id,version['preview_version'])
        transition=folder/'veo_transition.mp4';intro=folder/'intro.mp4'
        motifs={'light':'Soft volumetric light sweeping over abstract polished surfaces.',
            'signal':'Luminous particles traveling through abstract wave fields.',
            'optics':'Abstract rays refracting through floating glass prisms.'}
        prompt=motifs[version['veo_transition']]+' Premium cinematic 3D transition, dark clean studio, restrained teal accents, slow orbit and strong depth. No product, device, logo, text, people or specific engineering parts. Abstract visual metaphor only.'
        progress(idea_id,'Video',number,'Veo로 추상 전환 컷을 제작합니다. 제품 원본은 보존합니다.')
        await asyncio.to_thread(generate_video_clip,prompt=prompt,output_path=transition,duration_seconds=4,aspect_ratio='9:16')
        await asyncio.to_thread(subprocess.run,[get_ffmpeg_bin(),'-v','error','-i',str(transition),'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-map','0:v:0','-map','1:a:0','-vf',f'scale={width}:{height},setsar=1,fps=24','-t','4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(intro)],check=True,capture_output=True,timeout=240)
        clips.append(intro)
    for idx,scene in enumerate(board['scenes'],1):
        progress(idea_id,'Video',number,f'{idx}/6 컷 영상·음성을 만듭니다.')
        audio=folder/f'audio_{idx:02d}.mp3'
        await synthesize_speech(scene['narration_ko'],audio,voice=DEFAULT_VOICE)
        result=await asyncio.to_thread(subprocess.run,['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(audio)],capture_output=True,text=True,timeout=30)
        duration=max(4,float(result.stdout.strip())+.3)
        raw=folder/f'raw_{idx:02d}.mp4'
        if scene['visual_mode']=='official_clip':
            source=preview_folder/f'scene_{idx:02d}.mp4'
            if scene.get('enhance_3d'):
                if not model_folder:raise ValueError('3D 보완 모델이 필요합니다.')
                # Preserve official footage first, then add the approved exterior macro/orbit.
                base=folder/f'base_{idx:02d}.mp4';extra=folder/f'3d_{idx:02d}.mp4'
                camera=scene.get('camera_settings') or dict(distance=5.4,elevation=1.25,end_angle=65)
                if store.get(idea_id,'3DModel',model_number).get('kind')=='principle':
                    camera=dict(camera,distance=max(7.5,camera.get('distance',5.4)))
                await asyncio.to_thread(blender.clip,model_folder/'model.blend',extra,camera.get('start_angle',25),duration*.4,
                    camera_settings=camera)
                vf=f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,tpad=stop_mode=clone:stop_duration={duration}'
                await asyncio.to_thread(subprocess.run,[get_ffmpeg_bin(),'-v','error','-i',str(source),'-vf',vf,'-t',str(duration*.6),'-an','-c:v','libx264','-pix_fmt','yuv420p',str(base)],check=True,capture_output=True,timeout=240)
                await asyncio.to_thread(subprocess.run,[get_ffmpeg_bin(),'-v','error','-i',str(base),'-i',str(extra),'-filter_complex','[0:v][1:v]concat=n=2:v=1:a=0[v]','-map','[v]','-an','-c:v','libx264','-pix_fmt','yuv420p',str(raw)],check=True,capture_output=True,timeout=240)
            else:shutil.copyfile(source,raw)
        elif scene['visual_mode']=='approved_model':
            await asyncio.to_thread(blender.clip,model_folder/'model.blend',raw,scene['camera_angle'],duration,camera_settings=scene.get('camera_settings'))
        elif scene['visual_mode']=='real_media':
            await asyncio.to_thread(render_source_clip,MediaSource(**scene['media_source']),raw,'9:16',4)
        elif scene.get('reference_scene_file'):
            await asyncio.to_thread(blender.clip,preview_folder/scene['reference_scene_file'],raw,scene.get('camera_angle',25),duration,
                camera_settings=dict(distance=scene.get('reference_camera_distance',5.8),elevation=.5,end_angle=scene.get('camera_angle',25)+25))
        else:
            await asyncio.to_thread(generate_video_clip,prompt=motion_prompt(scene),
                output_path=raw,duration_seconds=4,aspect_ratio='9:16',image_path=preview_folder/f'scene_{idx:02d}.png')
        output=folder/f'clip_{idx:02d}.mp4'
        filters=f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,tpad=stop_mode=clone:stop_duration={duration}'
        if scene.get('enhance_3d') and model_number and store.get(idea_id,'3DModel',model_number).get('kind')=='principle':
            filters+=f",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='PRINCIPLE VISUAL - NOT ACTUAL GEOMETRY':fontsize={max(10,width//42)}:fontcolor=white:box=1:boxcolor=black@0.7:x=(w-tw)/2:y=h*0.88:enable='gte(t,{duration*.6})'"
        cmd=[get_ffmpeg_bin(),'-v','error','-i',str(raw),'-i',str(audio),'-map','0:v:0','-map','1:a:0',
            '-vf',filters,
            '-af','apad','-t',str(duration),'-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2',str(output)]
        mux=await asyncio.to_thread(subprocess.run,cmd,capture_output=True,timeout=240)
        if mux.returncode: raise ValueError('음성·영상 합성에 실패했습니다.')
        clips.append(output)
    listing=folder/'clips.txt';listing.write_text('\n'.join(f"file '{p.name}'" for p in clips),encoding='utf-8')
    output=folder/'final.mp4'
    joined=await asyncio.to_thread(subprocess.run,[get_ffmpeg_bin(),'-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(output)],capture_output=True,timeout=180)
    if joined.returncode: raise ValueError('최종 영상 합성에 실패했습니다.')
    model=store.get(idea_id,'3DModel',model_number) if model_number else {}
    credits=folder/'sources.json';store.write_json(credits,dict(product_url=version['product_url'],model_source=model.get('selected_source'),media=model.get('sources',[]),research=idea['recommendation']['sources'],feature_references=[dict(scene_number=s['scene_number'],references=s.get('feature_references',[]),limitation=s.get('reference_limitation','')) for s in board['scenes']]))
    if (preview_folder/'source.json').exists():
        provenance=json.loads(credits.read_text(encoding='utf-8'))
        provenance['official_video']=json.loads((preview_folder/'source.json').read_text(encoding='utf-8'))
        provenance['clip_intervals']=[dict(start=s.get('start_seconds'),end=s.get('end_seconds'),feature=s['purpose']) for s in board['scenes']]
        store.write_json(credits,provenance)
    store.update(idea_id,'Video',number,status='ready',output_url=store.url(output),sources_url=store.url(credits),message='영상이 완성됐습니다.')
