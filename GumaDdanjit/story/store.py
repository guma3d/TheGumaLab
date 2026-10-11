import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.lock = threading.RLock()
        for folder in ('assets', 'imports', 'thumbs', 'exports'):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS scripts (id TEXT, version INTEGER, data TEXT NOT NULL, PRIMARY KEY(id, version));
                CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, data TEXT NOT NULL);
            ''')

    def connect(self):
        db = sqlite3.connect(self.root / 'gumastory.sqlite3', timeout=30)
        db.execute('PRAGMA journal_mode=WAL')
        return db

    def assets(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT data FROM assets ORDER BY id')]

    def asset(self, asset_id):
        with self.connect() as db:
            row = db.execute('SELECT data FROM assets WHERE id=?', (asset_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def add_asset(self, item):
        path = self.root / 'assets' / item['file']
        if Path(item['file']).name != item['file'] or not path.is_file():
            raise ValueError('잘못된 원본 파일')
        with path.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        item = dict(item, sha256=digest, bytes=path.stat().st_size,
                    created_at=now(), revision=1, archived=item.get('archived', False), note=item.get('note', ''), tags=item.get('tags', []))
        if path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
            with Image.open(path) as im:
                item['width'], item['height'] = im.size
                item['media'] = 'image'
                thumb = ImageOps.exif_transpose(im).convert('RGB')
                thumb.thumbnail((640, 400))
                thumb.save(self.root / 'thumbs' / (item['id'] + '.jpg'), quality=85)
        else:
            item['media'] = 'video' if path.suffix == '.mp4' else 'audio'
        with self.connect() as db:
            db.execute('INSERT INTO assets VALUES (?,?)', (item['id'], json.dumps(item, ensure_ascii=False)))
        return item

    def ingest(self):
        with self.lock:
            for file in sorted((self.root / 'imports').glob('*.json')):
                item = json.loads(file.read_text(encoding='utf-8-sig'))
                if not self.asset(item['id']):
                    self.add_asset(item)

    def update_asset(self, asset_id, expected, patch):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM assets WHERE id=?', (asset_id,)).fetchone()
            if not row:
                raise KeyError(asset_id)
            old = json.loads(row[0])
            if old['revision'] != expected:
                raise ValueError('다른 곳에서 수정됐습니다. 새로고침 후 다시 저장해주세요.')
            new = dict(old, **patch, revision=expected + 1, updated_at=now())
            db.execute('UPDATE assets SET data=? WHERE id=?', (json.dumps(new, ensure_ascii=False), asset_id))
        return new

    def scripts(self):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT data FROM scripts ORDER BY id, version DESC')]

    def save_script(self, script_id, expected, data):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            latest = db.execute('SELECT MAX(version) FROM scripts WHERE id=?', (script_id,)).fetchone()[0] or 0
            if latest != expected:
                raise ValueError('새 버전이 이미 있습니다. 새로고침 후 다시 저장해주세요.')
            item = dict(data, id=script_id, version=latest + 1, saved_at=now())
            db.execute('INSERT INTO scripts VALUES (?,?,?)', (script_id, latest + 1, json.dumps(item, ensure_ascii=False)))
        return item

    def profile(self, char_id):
        with self.connect() as db:
            r = db.execute('SELECT data FROM profiles WHERE id=?', (char_id,)).fetchone()
        return json.loads(r[0]) if r else {}

    def save_profile(self, char_id, data):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO profiles VALUES (?,?)', (char_id, json.dumps(data, ensure_ascii=False)))


def seed_script(store):
    if store.scripts():
        return
    titles = [(0, 120, '승진 제안과 망설임'), (120, 360, '보상과 달라지는 하루'),
              (360, 660, '시간·책임·관계의 고민'), (660, 900, '거절했을 때의 대가'),
              (900, 1080, '받아들이기 좋은 조건'), (1080, 1200, '처음의 질문으로 돌아오기')]
    store.save_script('promotion', 0, dict(title='승진을 거절하는 사람들은 무엇을 계산했을까?',
        summary='20분 시험 편. 화면 없이도 이해되는 대본과 편안한 내레이션. 제목의 전제와 사례는 조사 전입니다.',
        status='outline', note='합의한 구성 초안입니다. 완성 대본·사실 검증·제작 승인이 아닙니다.',
        scenes=[dict(start=a, end=b, title=t, narration='', visual='', source='', asset_ids=[]) for a,b,t in titles]))
