"""Append-only standalone cover images, linked to an exact video version."""
import shutil
from pathlib import Path
from PIL import Image
from app.core import versions as store
from app.core.prepared_packages import digest
from app.core.recommendations import now_kst


def history(idea_id):
    import json
    return [json.loads(p.read_text(encoding='utf-8')) for p in
            sorted((store.directory(idea_id)/'Thumbnail').glob('v*/metadata.json'),reverse=True)]


def register(idea_id, video_version, source, provenance):
    video=store.get(idea_id,'Video',video_version)
    if video['status']!='ready':
        raise ValueError('완성 영상 버전을 지정하세요.')
    if provenance.get('reviewed') is not True or not provenance.get('source_kind'):
        raise ValueError('썸네일 출처·검수 기록이 필요합니다.')
    source=Path(source)
    with Image.open(source) as im:
        width,height=im.size
        if im.format not in ('PNG','JPEG','WEBP') or min(width,height)<720:
            raise ValueError('720px 이상 검수된 이미지가 필요합니다.')
        suffix={'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}[im.format]
        im.verify()
    with store.LOCK:
        old=history(idea_id);number=max((x['number'] for x in old),default=0)+1
        folder=store.directory(idea_id)/'Thumbnail'/f'v{number:04d}'
        folder.mkdir(parents=True,exist_ok=False)
        target=folder/('cover'+suffix);shutil.copyfile(source,target)
        value=dict(number=number,video_version=video_version,image_url=store.url(target),
                   file_sha256=digest(target),width=width,height=height,
                   created_at=now_kst().isoformat(),provenance=provenance,
                   youtube_applied=False)
        store.write_json(folder/'metadata.json',value)
        store.update(idea_id,'Video',video_version,thumbnail_url=value['image_url'],thumbnail_version=number)
        return value
