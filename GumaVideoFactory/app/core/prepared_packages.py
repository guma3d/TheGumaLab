"""Codex prepares locally; only a sealed, reviewed package can enter paid video."""
import hashlib
import json
import math
import shutil
from pathlib import Path
from app.core import versions as store
from app.core import official_clips as clips
from app.core.production_rules import snapshot
from app.core.recommendations import now_kst


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def prepare(rec,day,regenerate=False):
    idea=store.create(rec,day,approved=False);id=idea['id']
    previous=store.history(id,'Preview')
    if not regenerate and previous and previous[0].get('execution_mode')=='codex_scheduled' and previous[0]['status'] in ('awaiting_review','ready'):
        return dict(id=id,version=previous[0]['number'],status=previous[0]['status'])
    value,_=store.reserve(id,'Preview',regenerate=True,execution_mode='codex_scheduled')
    n=value['number'];folder=store.version_dir(id,'Preview',n)
    try:
        rules=snapshot('tech');store.write_json(folder/'production_rules.json',rules)
        cached=clips.reuse_source(id,n,rec['technical_video'],folder)
        path,meta=cached if cached else clips.download(rec['technical_video'],folder)
        step=max(1,meta['duration']/64)
        clips.sheets(path,[i*step for i in range(math.ceil(meta['duration']/step)) if i*step<meta['duration']-.1],folder,'overview')
        store.update(id,'Preview',n,status='awaiting_review',message='Codex가 기능·구간·3D를 검토 중입니다.',production_rules_revision=rules['revision'],production_rules_sha256=rules['sha256'])
        return dict(id=id,version=n,folder=str(folder),source_sha256=meta['sha256'])
    except Exception:
        store.update(id,'Preview',n,status='failed',message='공식 원본 준비 실패 · 다음 조사에서 자료를 재확인합니다.')
        raise


def draft(id,n,board_path):
    folder=store.version_dir(id,'Preview',n);v=store.get(id,'Preview',n)
    if v['status']!='awaiting_review' or (folder/'storyboard.json').exists():raise ValueError('새 준비 버전을 사용해주세요.')
    meta=read(folder/'source.json')
    if digest(folder/'source.mp4')!=meta['sha256']:raise ValueError('원본 해시 불일치')
    board=clips.ClipBoard.model_validate(read(board_path))
    clips.validate_board(board,meta['duration'],store.read(id)['recommendation'])
    store.write_json(folder/'analysis.json',board.model_dump())
    result=clips.render_board(id,n,board,folder/'source.mp4',meta,lambda _:None,publish=False)
    for i,s in enumerate(board.scenes,1):
        length=s.end_seconds-s.start_seconds
        clips.sheets(folder/f'scene_{i:02d}.mp4',[0,length*.25,length*.5,length*.75,length-.12],folder,f'check_{i:02d}')
    return dict(board_sha256=digest(folder/'storyboard.json'),scenes=len(result['scenes']))


def add_model(id,n,source,metadata):
    """Trusted local build or inspected public asset. No provider APIs."""
    from app.core import blender_runner as blender
    preview=store.get(id,'Preview',n)
    if preview['status']!='awaiting_review':raise ValueError('준비 중인 프리뷰만 모델을 연결할 수 있습니다.')
    if metadata.get('kind') not in ('downloaded','reconstructed','principle'):raise ValueError('모델 종류가 필요합니다.')
    if not metadata.get('sources') or not metadata.get('limitation'):raise ValueError('출처·형상 검증 한계를 기록해주세요.')
    value,_=store.reserve(id,'3DModel',True,preview_version=n,execution_mode='codex_scheduled')
    m=value['number'];folder=store.version_dir(id,'3DModel',m)
    try:
        rules=snapshot('tech');store.write_json(folder/'production_rules.json',rules)
        asset=folder/('source'+Path(source).suffix);shutil.copyfile(source,asset)
        if metadata['kind']=='principle':
            blender.run_blender(folder,'--source',asset,'--output',folder,'--product-name',store.read(id)['title'],'--distance',7.5)
        else:blender.build(folder,source=asset,product_name=store.read(id)['title'])
        store.write_json(folder/'sources.json',metadata)
        store.update(id,'3DModel',m,status='awaiting_review',kind=metadata['kind'],model_sha256=digest(folder/'model.blend'),
            images=[store.url(folder/f'view_{i}.png') for i in range(1,5)],model_url=store.url(folder/'model.blend'),
            uncertainties=[metadata['limitation']],sources_url=store.url(folder/'sources.json'),message='Codex 모델 외형·원리 검증 중')
        return dict(number=m,folder=str(folder),sha256=digest(folder/'model.blend'))
    except Exception:
        store.update(id,'3DModel',m,status='failed',message='로컬 모델 준비 실패')
        raise


def seal(id,n,review_path):
    folder=store.version_dir(id,'Preview',n);v=store.get(id,'Preview',n)
    if v['status']!='awaiting_review':raise ValueError('완성 버전은 수정할 수 없습니다.')
    board=read(folder/'storyboard.json');review=read(review_path);meta=read(folder/'source.json')
    if review.get('reviewed_by')!='codex' or review.get('passed') is not True:raise ValueError('Codex 실물·기능 검수가 필요합니다.')
    if review.get('source_sha256')!=digest(folder/'source.mp4') or review['source_sha256']!=meta['sha256'] or review.get('board_sha256')!=digest(folder/'storyboard.json'):raise ValueError('검토 대상 해시 불일치')
    checks=review.get('scenes',[])
    if len(checks)!=len(board['scenes']) or any(c.get('number')!=i or not all(c.get(k) is True for k in ('feature_match','correct_product','clean_boundaries')) or not c.get('notes') for i,c in enumerate(checks,1)):raise ValueError('모든 클립 검토가 필요합니다.')
    models=store.history(id,'3DModel');model=next((m for m in models if m.get('preview_version')==n),None)
    files={}
    if board['needs_3d']:
        if not model or model['status'] not in ('ready','awaiting_review'):raise ValueError('3D 모델 준비가 끝나지 않았습니다.')
        modeldir=store.version_dir(id,'3DModel',model['number']);mr=review.get('model',{})
        if mr.get('sha256')!=digest(modeldir/'model.blend') or mr.get('passed') is not True or not mr.get('notes'):raise ValueError('네 방향 모델 검토가 필요합니다.')
        if model.get('kind')=='principle':
            for s in board['scenes']:
                if s.get('enhance_3d') and '원리' not in s.get('enhancement_reason',''):raise ValueError('원리 모델임을 콘티에 명시해주세요.')
        for p in [modeldir/'model.blend',modeldir/'sources.json',*[modeldir/f'view_{i}.png' for i in range(1,5)]]:files[p.relative_to(store.directory(id)).as_posix()]=digest(p)
    for p in [folder/'source.mp4',folder/'source.json',folder/'storyboard.json',*[folder/f'scene_{i:02d}.{ext}' for i in range(1,len(board['scenes'])+1) for ext in ('png','mp4')]]:files[p.relative_to(store.directory(id)).as_posix()]=digest(p)
    transition=review.get('veo_transition')
    if transition not in ('light','signal','optics'):raise ValueError('Veo 전환 연출 light/signal/optics를 선택해주세요.')
    store.write_json(folder/'visual_review.json',review)
    files[(folder/'visual_review.json').relative_to(store.directory(id)).as_posix()]=digest(folder/'visual_review.json')
    store.write_json(folder/'package.json',dict(files=files,reviewed_by='codex',prepared_at=now_kst().isoformat(),model_version=model['number'] if board['needs_3d'] else None,veo_transition=transition))
    if board['needs_3d']:store.update(id,'3DModel',model['number'],status='ready',prepared_by='codex',quality_reviewed_at=now_kst().isoformat(),message='사전 3D 검증 완료 · 최종 확인에 포함')
    return store.update(id,'Preview',n,status='ready',storyboard=board,needs_3d=board['needs_3d'],package_ready=True,model_version=model['number'] if board['needs_3d'] else None,message='제작 준비 완료 · 클립·대본·3D 확인 후 Veo 제작')


def verify_package(id,n):
    path=store.version_dir(id,'Preview',n)/'package.json'
    if not path.is_file():raise ValueError('예약 사전 준비·검증이 완료되어야 합니다.')
    package=read(path)
    if not package.get('files'):raise ValueError('준비 자료가 없습니다.')
    for name,sha in package['files'].items():
        p=(store.directory(id)/name).resolve()
        if not p.is_relative_to(store.directory(id).resolve()) or not p.is_file() or digest(p)!=sha:raise ValueError('검증한 준비 자료가 변경되었습니다. 재검토가 필요합니다.')
    return package
