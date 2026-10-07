"""Local, silent storyboard previews. No paid model calls or publishing."""
import hashlib
import subprocess
import tempfile
import uuid
from pathlib import Path

from app.store import now


def render_preview(store, job_id, project, release):
    job = store.get('jobs', job_id)
    output = store.root / 'media' / (uuid.uuid4().hex + '.mp4')
    try:
        job = store.save('jobs', dict(job, status='running', message='컷을 세로 영상으로 변환하고 있어요.'), job_id, job['revision'])
        with tempfile.TemporaryDirectory(prefix='gumashop-render-') as directory:
            folder = Path(directory)
            for index, cut in enumerate(project['cuts']):
                asset = store.get('assets', cut['asset_id'])
                source = store.root / 'media' / asset['filename']
                args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
                args += ['-loop', '1'] if asset['kind'] == 'image' else ['-stream_loop', '-1']
                if asset['kind'] == 'video':
                    args += ['-protocol_whitelist', 'file,pipe', '-f', 'matroska' if source.suffix == '.webm' else 'mov']
                args += ['-i', str(source), '-t', str(cut['seconds']), '-vf',
                         'scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=0xf3f2ec,setsar=1,fps=24',
                         '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '22',
                         '-pix_fmt', 'yuv420p', str(folder / f'cut{index:02d}.mp4')]
                subprocess.run(args, capture_output=True, check=True, timeout=180)
                job = store.save('jobs', dict(job, message=f'{index + 1}/{len(project["cuts"])}컷 준비 완료'), job_id, job['revision'])
            concat = folder / 'cuts.txt'
            concat.write_text('\n'.join(f"file 'cut{i:02d}.mp4'" for i in range(len(project['cuts']))), encoding='utf-8')
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '1',
                            '-i', str(concat), '-c', 'copy', '-movflags', '+faststart', str(output)],
                           capture_output=True, check=True, timeout=60)
        with output.open('rb') as file:
            digest = hashlib.file_digest(file, 'sha256').hexdigest()
        video = store.save('videos', dict(filename=output.name, original_name='gumashop-storyboard-preview.mp4',
            kind='video', bytes=output.stat().st_size, sha256=digest, duration=sum(c['seconds'] for c in project['cuts']),
            project_id=project['id'], storyboard_revision=project['revision'], storyboard=project,
            note='콘티 프리뷰 · 720×1280 · 24fps · 무음. 대사, 음성, 자막, AI 동작 생성은 포함되지 않습니다.',
            status='review', review=None, is_preview=True))
        store.save('jobs', dict(job, status='complete', message='콘티 프리뷰가 완성됐어요.', video_id=video['id'], finished_at=now()), job_id, job['revision'])
    except Exception:
        output.unlink(missing_ok=True)
        latest = store.get('jobs', job_id)
        store.save('jobs', dict(latest, status='failed', message='프리뷰 제작에 실패했어요. 컷의 미디어 파일과 길이를 확인 후 다시 시도해주세요.', finished_at=now()), job_id, latest['revision'])
    finally:
        release()
