"""Product workspaces. Outputs are append-only; each version owns its parents."""
import hashlib
import json
import os
import re
import threading
import uuid
from pathlib import Path
from app.config import STORAGE_DIR
from app.core.recommendations import now_kst

ROOT = STORAGE_DIR / 'products'
LOCK = threading.RLock()
STAGES = ('3DModel', 'Preview', 'Video')


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)


def directory(idea_id):
    if not re.fullmatch(r'[a-f0-9]{16}', idea_id):
        raise ValueError('아이디어를 찾을 수 없습니다.')
    return ROOT / idea_id


def read(idea_id):
    return json.loads((directory(idea_id) / 'idea.json').read_text(encoding='utf-8'))


def create(recommendation, day):
    # The same recommended product on different days continues its workspace.
    identity = recommendation['category'] + ':' + recommendation['subject'].strip().casefold()
    idea_id = hashlib.sha256(identity.encode()).hexdigest()[:16]
    with LOCK:
        path = directory(idea_id) / 'idea.json'
        if path.exists():
            return read(idea_id)
        value = dict(id=idea_id, recommendation= recommendation, date=day,
                     category=recommendation['category'], title=recommendation['subject'],
                     created_at=now_kst().isoformat(), idea_approved_at=now_kst().isoformat())
        for stage in STAGES:
            (directory(idea_id) / stage).mkdir(parents=True, exist_ok=True)
        write_json(path, value)
        return value


def version_dir(idea_id, stage, number):
    if stage not in STAGES or not isinstance(number, int) or not 1 <= number <= 999999:
        raise ValueError('잘못된 버전입니다.')
    return directory(idea_id) / stage / f'v{number:04d}'


def get(idea_id, stage, number):
    return json.loads((version_dir(idea_id, stage, number) / 'version.json').read_text(encoding='utf-8'))


def history(idea_id, stage):
    result = []
    for path in sorted((directory(idea_id) / stage).glob('v*/version.json'), reverse=True):
        result.append(json.loads(path.read_text(encoding='utf-8')))
    return sorted(result, key=lambda v: v['number'], reverse=True)


def reserve(idea_id, stage, regenerate=False, **parents):
    with LOCK:
        read(idea_id)
        old = history(idea_id, stage)
        if any(v['status'] == 'running' for s in STAGES for v in history(idea_id, s)):
            raise ValueError('제작 중입니다. 완료 후 다시 실행해주세요.')
        if old and not regenerate:
            return old[0], False
        number = max((v['number'] for v in old), default=0) + 1
        folder = version_dir(idea_id, stage, number)
        folder.mkdir(parents=True, exist_ok=False)
        value = dict(number=number, stage=stage, status='running', approved_at=None,
                     created_at=now_kst().isoformat(), message='작업 준비 중')
        value.update(parents)
        write_json(folder / 'version.json', value)
        return value, True


def update(idea_id, stage, number, **fields):
    with LOCK:
        value = get(idea_id, stage, number)
        value.update(fields)
        write_json(version_dir(idea_id, stage, number) / 'version.json', value)
        return value


def snapshot(idea_id):
    idea = read(idea_id)
    idea['versions'] = {s: history(idea_id, s) for s in STAGES}
    return idea


def listing(category):
    rows = []
    for path in ROOT.glob('*/idea.json'):
        value = json.loads(path.read_text(encoding='utf-8'))
        if value['category'] == category:
            rows.append(value)
    return sorted(rows, key=lambda x: x['created_at'], reverse=True)


def url(path):
    return '/storage/' + Path(path).resolve().relative_to(STORAGE_DIR.resolve()).as_posix()


def recover_interrupted():
    # Single uvicorn worker. A restart cannot silently leave an in-memory job running.
    with LOCK:
        for path in ROOT.glob('*/*/v*/version.json'):
            value = json.loads(path.read_text(encoding='utf-8'))
            if value.get('status') == 'running':
                value.update(status='failed', message='서버 재시작으로 중단됐습니다. 재생성하면 새 버전으로 시작합니다.')
                write_json(path, value)


def link_legacy(projects):
    """Previously selected recommendations remain discoverable; do not render."""
    for project in projects:
        rec=project.get('recommendation') or {}
        if not all(rec.get(k) for k in ('subject','category','product_keyword','hook')):
            continue
        with LOCK:
            idea=create(rec,project.get('recommendation_date',project['created_at'][:10]))
            ids=idea.setdefault('legacy_project_ids',[])
            if project['id'] not in ids:
                ids.append(project['id'])
                write_json(directory(idea['id'])/'idea.json',idea)


def workflow(idea):
    """Current version state for cards; a new model never inherits approval."""
    if idea['category']=='tech':return clip_workflow(idea)
    stages = {s: history(idea['id'], s) for s in STAGES}
    latest = {s: rows[0] if rows else None for s, rows in stages.items()}
    model, preview, video = (latest[s] for s in STAGES)
    names = {'3DModel': '모델' if idea['category']=='tech' else '실사 자료', 'Preview': '프리뷰', 'Video': '영상'}
    next_stage = '3DModel'
    message = '다음: ' + names['3DModel'] + ' 준비'
    if model and model['status']=='ready':
        if model.get('approved_at'):
            next_stage = 'Preview'; message = '다음: 프리뷰 생성'
            if preview and preview['status']=='ready':
                next_stage = 'Video'; message = '다음: 최종 확인·영상 제작'
                if preview.get('model_version') != model['number']:
                    next_stage = 'Preview'; message = '이전 모델 프리뷰 · 버전 확인 필요'
                elif video and video['status']=='ready' and video.get('preview_version')==preview['number']:
                    message = '영상 완성 · 결과 확인'
        else:
            message = '다음: ' + names['3DModel'] + ' 확인·승인'
    running = next((s for s in STAGES if latest[s] and latest[s]['status']=='running'), None)
    if running:
        next_stage = running; message = names[running] + ' 생성 중'
    buttons = []
    for stage in STAGES:
        v = latest[stage]
        allowed = stage=='3DModel' or bool(model and model['status']=='ready' and model.get('approved_at'))
        if stage=='Video': allowed = allowed and bool(preview and preview['status']=='ready')
        label = {'3DModel': 'Generate 3D Model' if idea['category']=='tech' else 'Prepare Real Media', 'Preview': 'Generate Preview', 'Video': 'Create Video'}[stage]
        state = '대기'
        if v:
            state = {'running':'생성 중','failed':'실패','ready':'확인 대기'}.get(v['status'],'대기')
            if v['status']=='ready':
                state = '승인 완료' if stage=='3DModel' and v.get('approved_at') else ('완료' if stage=='Video' else '확인 대기')
                label = names[stage] + (' 보기' if state in ('승인 완료','완료') else ' 확인·승인')
            elif v['status']=='running': label = names[stage] + ' 생성 중'
            elif v['status']=='failed': label = names[stage] + ' 오류 확인'
        buttons.append(dict(stage=stage,label=label,state=state,number=v['number'] if v else None,
            status=v['status'] if v else 'empty',progress_message=v.get('message','') if v else '',
            primary=stage==next_stage,disabled=bool(running) or not allowed or bool(v and v['status']=='ready'),
            regen_disabled=not allowed or bool(running),existing=bool(v)))
    return dict(id=idea['id'],message=message,buttons=buttons,running=bool(running),
        approved=bool(model and model['status']=='ready' and model.get('approved_at')))


def clip_workflow(idea):
    latest={s:next(iter(history(idea['id'],s)),None) for s in STAGES}
    preview=latest['Preview'];model=latest['3DModel'];video=latest['Video']
    ready=bool(preview and preview['status']=='ready')
    needs=bool(ready and preview.get('needs_3d'))
    model_ok=bool(model and model['status']=='ready' and model.get('approved_at') and ready and model.get('preview_version')==preview['number'])
    next_stage='Preview';message='다음: 프리뷰·클립 생성'
    if ready:
        next_stage='3DModel' if needs and not model_ok else 'Video'
        message='3D모델 생성 필요' if next_stage=='3DModel' else '다음: 최종 확인·영상 제작'
        if needs and model and model['status']=='ready' and model.get('preview_version')==preview['number'] and not model.get('approved_at'):
            message='다음: 3D 모델 확인·승인'
        if video and video['status']=='ready' and video.get('preview_version')==preview['number'] and (not needs or video.get('model_version')==(model or {}).get('number')):
            message='영상 완성 · 결과 확인'
    running=next((s for s,v in latest.items() if v and v['status']=='running'),None)
    names={'Preview':'프리뷰·클립','3DModel':'3D 모델','Video':'영상'}
    if running:next_stage=running;message=names[running]+' 생성 중'
    buttons=[]
    for stage in ('Preview','3DModel','Video'):
        v=latest[stage];allowed=stage=='Preview' or (ready and (needs if stage=='3DModel' else not needs or model_ok))
        stale=bool(stage=='3DModel' and v and ready and v.get('preview_version')!=preview['number'])
        state='대기' if not v else {'running':'생성 중','failed':'실패','ready':'완료'}[v['status']]
        if stage=='3DModel':state='이전 프리뷰 모델' if stale else '승인 완료' if model_ok else '불필요' if ready and not needs else '확인 대기' if v and v['status']=='ready' else state
        buttons.append(dict(stage=stage,state=state,label=names[stage],number=v['number'] if v else None,
            status=v['status'] if v else 'empty',progress_message=v.get('message','') if v else '',primary=stage==next_stage,
            disabled=bool(running) or not allowed or bool(v and v['status']=='ready'),regen_disabled=bool(running) or not allowed,existing=bool(v)))
    return dict(id=idea['id'],message=message,buttons=buttons,running=bool(running),approved=model_ok,needs_3d=needs)
