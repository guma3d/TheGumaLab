"""Transactional JSON records with optimistic locking and immutable snapshots."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import HTTPException


def now():
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds')


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / 'media').mkdir(exist_ok=True)
        self.path = self.root / 'studio.sqlite3'
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS records (
                    kind TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL,
                    PRIMARY KEY(kind, id));
                CREATE TABLE IF NOT EXISTS history (
                    kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL,
                    data TEXT NOT NULL, PRIMARY KEY(kind, id, revision));
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def all(self, kind):
        with self.connect() as db:
            rows = db.execute('SELECT data FROM records WHERE kind=? ORDER BY rowid DESC', (kind,)).fetchall()
        return [json.loads(row['data']) for row in rows]

    def get(self, kind, key):
        with self.connect() as db:
            row = db.execute('SELECT data FROM records WHERE kind=? AND id=?', (kind, key)).fetchone()
        if not row:
            raise HTTPException(404, '항목을 찾을 수 없습니다.')
        return json.loads(row['data'])

    def save(self, kind, data, key=None, revision=None):
        key = key or uuid.uuid4().hex
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM records WHERE kind=? AND id=?', (kind, key)).fetchone()
            old = json.loads(row['data']) if row else None
            if (old and revision != old['revision']) or (not old and revision is not None):
                raise HTTPException(409, '다른 창에서 변경됐습니다. 새로고침 후 다시 저장해주세요.')
            stamp = now()
            value = dict(data, id=key, revision=(old['revision'] + 1 if old else 1),
                         created_at=old['created_at'] if old else stamp, updated_at=stamp)
            encoded = json.dumps(value, ensure_ascii=False)
            db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (kind, key, encoded))
            db.execute('INSERT INTO history VALUES (?,?,?,?)', (kind, key, value['revision'], encoded))
        return value

    def history(self, kind, key):
        self.get(kind, key)
        with self.connect() as db:
            rows = db.execute('SELECT data FROM history WHERE kind=? AND id=? ORDER BY revision DESC', (kind, key)).fetchall()
        return [json.loads(row['data']) for row in rows]


FAMILY = [
    dict(id='tiger', name='호랑이 아빠', species='호랑이', role='똑똑한 과학자', categories=['tech'],
         personality='새로운 기술이 궁금한 아빠. 가족에게 쓸모 있는 물건을 찾아요.',
         appearance='호랑이 무늬와 가족 간 키 비율을 먼저 정해주세요.', room='아빠의 작업실',
         voice='미정', rules='제품 구조와 작동 방식을 정확하게 표현하기', color='amber'),
    dict(id='rabbit', name='토끼 엄마', species='토끼', role='요리와 살림의 전문가', categories=['food', 'living'],
         personality='맛있는 요리와 편리한 일상을 좋아하는 엄마.',
         appearance='귀 모양, 털 색상, 기본 의상을 먼저 정해주세요.', room='따뜻한 주방',
         voice='미정', rules='실제 제품의 조리법과 사용법 확인하기', color='sage'),
    dict(id='pig', name='돼지 큰아들', species='돼지', role='먹는 즐거움에 진심인 미식가', categories=['food'],
         personality='맛과 식감, 새로운 음식 조합에 관심이 많아요.',
         appearance='통통한 체형. 외형과 나이는 아직 미확정.', room='가족의 식탁',
         voice='미정', rules='가상의 시식을 실제 사용 후기처럼 표현하지 않기', color='rose'),
    dict(id='cat', name='고양이 작은딸', species='고양이', role='뷰티와 생활의 취향 큐레이터', categories=['beauty', 'living'],
         personality='꾸미기를 좋아하고 자기만의 취향을 찾아가는 딸.',
         appearance='털 무늬, 귀 모양, 기본 의상과 나이는 아직 미확정.', room='작은 드레스룸',
         voice='미정', rules='색상과 사용감을 실제 자료에 근거해 소개하기', color='lavender'),
]


def seed(store):
    known = {v['id'] for v in store.all('characters')}
    for item in FAMILY:
        if item['id'] not in known:
            store.save('characters', dict(item, reference_id='', archived=False), item['id'])
