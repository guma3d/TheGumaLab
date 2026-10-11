"""Read-only, shared presentation of the three existing version stores."""
import json
import re
from pathlib import Path

PREFIX = '/gumaddanjit'


def catalog(versions, story_store, shop_store):
    rows = []
    project_titles = {}

    def add(section, group, project, title, version, key, **fields):
        rows.append(dict(section=section, group=group, project=project, title=title,
                         version=version, key=key, **fields))

    def short_url(value):
        if not value:
            return ''
        return PREFIX + '/shorts' + value if value.startswith('/storage/') else value

    for file in sorted(versions.ROOT.glob('*/idea.json')):
        idea = json.loads(file.read_text(encoding='utf-8'))
        if idea.get('archived'):
            continue
        pid, title = idea['id'], idea['title']
        project_titles['shorts:' + pid] = title
        resource = idea.get('recommendation', {})
        add('shorts', 'resources', pid, title, 1, pid + ':resource',
            text=resource.get('key_feature', ''), sources=resource.get('sources', []))
        for stage, group in [('Preview', 'concepts'), ('Video', 'videos')]:
            for v in versions.history(pid, stage):
                if stage == 'Video' and not v.get('output_url'):
                    continue
                folder = versions.version_dir(pid, stage, v['number'])
                images = [dict(title=s.get('narration_ko', '') or f'CUT {i+1}',
                               url=short_url(s.get('image_url', '')))
                          for i, s in enumerate(v.get('storyboard', {}).get('scenes', []))
                          if s.get('image_url')]
                add('shorts', group, pid, title, v['number'], f'{pid}:{stage}:{v["number"]}',
                    date=v.get('created_at', ''), images=images,
                    media_url=short_url(v.get('output_url', '')) if stage == 'Video' else '',
                    poster=short_url(v.get('thumbnail_url', '')), media='video',
                    text=v.get('storyboard', {}).get('summary', ''))
                if stage == 'Preview':
                    originals = [dict(title=p.name, url=short_url(versions.url(p)))
                                 for p in sorted(folder.glob('source_*'))
                                 if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')]
                    if originals:
                        add('shorts', 'resources', pid, title + ' · 원본 자료', v['number'],
                            f'{pid}:sources:{v["number"]}', images=originals,
                            date=v.get('created_at', ''))
        # Product references and original resources are retained alongside their versions.
        for stage in ['3DModel']:
            for v in versions.history(pid, stage):
                add('shorts', 'resources', pid, title, v['number'], f'{pid}:{stage}:{v["number"]}',
                    text=v.get('message', ''), media_url=short_url(v.get('output_url', '')),
                    media='image')

    scripts = story_store.scripts()
    for s in sorted(scripts, key=lambda s: s['version']):
        project_titles['story:' + s['id']] = s['title']
        text = '\n\n'.join(x.get('narration', '') or x.get('text', '') for x in s.get('scenes', []))
        add('story', 'resources', s['id'], s['title'], s['version'], f'script:{s["id"]}:{s["version"]}',
            date=s.get('saved_at', ''), text=(s.get('summary', '') + '\n\n' + text).strip(),
            download=PREFIX + f'/story/api/scripts/{s["id"]}/{s["version"]}/export')
    for a in story_store.assets():
        if a.get('archived'):
            continue
        group = 'videos' if a['media'] == 'video' else ('concepts' if a['media'] == 'image' and a.get('kind') in ('scene', 'chart') else 'resources')
        add('story', group, a.get('script_id') or a.get('parent_id') or a.get('character_id') or 'shared',
            a['title'], a.get('version', a.get('revision', 1)), a['id'], date=a.get('created_at', ''),
            media=a['media'], media_url=PREFIX + f'/story/media/{a["id"]}/original',
            download=PREFIX + f'/story/media/{a["id"]}/download',
            text=a.get('source', ''), parent=a.get('parent_id', ''))

    projects = {p['id']: p for p in shop_store.all('projects') if not p.get('archived')}
    project_titles.update({'shop:' + k: v['title'] for k, v in projects.items()})
    for kind, group in [('assets', 'resources'), ('videos', 'videos')]:
        counters = {}
        records = sorted(shop_store.all(kind), key=lambda a: a.get('created_at', ''))
        for a in records:
            if a.get('archived'):
                continue
            pid = a.get('project_id', 'shared')
            counters[pid] = counters.get(pid, 0) + 1
            number = counters[pid] if kind == 'videos' else a.get('generation_version', a.get('version', a.get('revision', 1)))
            item_group = 'concepts' if kind == 'videos' and a.get('is_preview') else group
            add('shop', item_group, pid, projects.get(pid, {}).get('title', a.get('title', a.get('original_name', '리소스'))),
                number, a['id'], date=a.get('created_at', ''),
                media='video' if kind == 'videos' else ('video' if a.get('kind') == 'video' else 'image'),
                media_url=PREFIX + f'/shop/api/{kind}/{a["id"]}/file',
                download=PREFIX + f'/shop/api/{kind}/{a["id"]}/file?download=true')
    assets = {a['id']: a for a in shop_store.all('assets')}
    for s in shop_store.all('storyboards'):
        if s['project_id'] not in projects:
            continue
        board = s.get('storyboard', {})
        images = [dict(title=c.get('narration', '') or f'CUT {i+1}',
                       url=PREFIX + f'/shop/api/assets/{c["asset_id"]}/file')
                  for i, c in enumerate(board.get('cuts', [])) if c.get('asset_id') in assets]
        add('shop', 'concepts', s['project_id'], projects[s['project_id']]['title'], s['number'], s['id'],
            date=s.get('created_at', ''), images=images, text=board.get('summary', ''))
    for row in rows:
        row['project_key'] = row['section'] + ':' + row['project']
        row['project_title'] = project_titles.get(row['project_key'],
            {'shared': '공통 리소스', 'adult-man': '성인 남성', 'adult-woman': '성인 여성',
             'boy': '남자 어린이', 'teen-girl': '여성 청소년'}.get(row['project'], row['project']))
        row['family'] = row['project'] if row['group'] == 'videos' else re.sub(r'\bv\d+\b', '', row['title'], flags=re.I).strip()
    return {'items': rows}
