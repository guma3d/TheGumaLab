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


def create(recommendation, day, approved=True):
    # The same recommended product on different days continues its workspace.
    identity = recommendation['category'] + ':' + recommendation['subject'].strip().casefold()
    idea_id = hashlib.sha256(identity.encode()).hexdigest()[:16]
    with LOCK:
        path = directory(idea_id) / 'idea.json'
        if path.exists():
            return read(idea_id)
        value = dict(id=idea_id, recommendation= recommendation, date=day,
                     category=recommendation['category'], title=recommendation['subject'],
                     created_at=now_kst().isoformat(), idea_approved_at=now_kst().isoformat() if approved else None)
        for stage in ('Preview','Video'):
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


def reserve(idea_id, stage, regenerate=False, queued=False, **parents):
    with LOCK:
        read(idea_id)
        old = history(idea_id, stage)
        if any(v['status'] in ('running','queued') for s in STAGES for v in history(idea_id, s)):
            raise ValueError('제작 중입니다. 완료 후 다시 실행해주세요.')
        if old and not regenerate:
            return old[0], False
        number = max((v['number'] for v in old), default=0) + 1
        folder = version_dir(idea_id, stage, number)
        folder.mkdir(parents=True, exist_ok=False)
        value = dict(number=number, stage=stage, status='queued' if queued else 'running', approved_at=None,
                     created_at=now_kst().isoformat(), message='제작 대기 중' if queued else '작업 준비 중')
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
    for stage, rows in idea['versions'].items():
        for value in rows:
            if value['status']=='queued':value['message']=queue_message(idea_id,stage,value)
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


def pending_jobs():
    jobs=[]
    for path in ROOT.glob('*/*/v*/version.json'):
        value=json.loads(path.read_text(encoding='utf-8'))
        if value.get('status') in ('queued','running'):
            jobs.append((path.parents[2].name,path.parents[1].name,value))
    return sorted(jobs,key=lambda job:(job[2]['created_at'],job[0],job[1],job[2]['number']))


def queue_message(idea_id, stage, value):
    waiting=[job for job in pending_jobs() if job[2]['status']=='queued']
    position=next((i for i,(idea,s,v) in enumerate(waiting,1) if (idea,s,v['number'])==(idea_id,stage,value['number'])),1)
    return f'제작 대기 · {position}번째'


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
    latest={stage:next(iter(history(idea['id'],stage)),None) for stage in ('Preview','Video')}
    preview=latest['Preview'];video=latest['Video']
    ready=bool(preview and preview.get('package_ready') and preview.get('storyboard',{}).get('pipeline')=='shopping_v2')
    message='09·15·21시 · 1개씩 자동 제작'
    if preview and not ready:message='새 쇼핑쇼츠 기준으로 재준비 필요'
    if ready:message='컷씬 완료 · 영상 자동 제작 준비'
    if video:message=video.get('message',message)
    running=any(v and v['status'] in ('running','queued') for v in latest.values())
    active=next(((stage,v) for stage,v in latest.items() if v and v['status'] in ('running','queued')),None)
    if active:
        stage,value=active
        message=queue_message(idea['id'],stage,value) if value['status']=='queued' else value.get('message','제작 중')
    buttons=[]
    for stage,v in latest.items():
        buttons.append(dict(stage=stage,label='컷씬' if stage=='Preview' else '영상',state=v.get('publication_state',v['status']) if v else '예약 준비',number=v['number'] if v else None,status=v['status'] if v else 'empty',progress_message=('이전 제작 방식 보관본' if stage=='Preview' and v and not ready else v.get('message','')) if v else '',primary=stage=='Video',disabled=stage!='Video' or not ready or running or bool(v and v['status']=='ready'),regen_disabled=stage!='Video' or not ready or running,existing=bool(v)))
    return dict(id=idea['id'],message=message,buttons=buttons,running=running,approved=False,needs_3d=False)


clip_workflow=workflow
