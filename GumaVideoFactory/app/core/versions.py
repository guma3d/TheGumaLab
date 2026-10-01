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
