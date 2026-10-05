"""Verified music library, narration-first mixing and lossless video preservation."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from app.config import STORAGE_DIR
from app.core import official_clips as media


def select(board):
    library = STORAGE_DIR / 'audio' / 'bgm'
    tracks = json.loads((library / 'manifest.json').read_text(encoding='utf-8-sig'))
    title = board.get('bgm_track')
    if not title:
        raise ValueError('콘티에 영상 분위기에 맞는 bgm_track을 지정하세요. 무음 완료는 허용하지 않습니다.')
    track = next((t for t in tracks if t['title'] == title), None)
    if not track:
        raise ValueError('검증된 BGM 목록에 없는 곡입니다.')
    path = (library / track['filename']).resolve()
    if path.parent != library.resolve() or not path.is_file():
        raise ValueError('BGM 원본이 없습니다.')
    if hashlib.sha256(path.read_bytes()).hexdigest().lower() != track['sha256'].lower():
        raise ValueError('BGM 원본 해시가 다릅니다.')
    if track.get('license') != 'CC BY 4.0' or not track.get('attribution'):
        raise ValueError('BGM 이용 근거와 크레딧이 필요합니다.')
    return path, track


def mix(source, output, board):
    path, track = select(board)
    seconds = media.duration(source)
    fade = min(1.0, seconds / 4)
    graph = (
        '[0:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[voice][key];'
        f'[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={seconds},'
        'asetpts=PTS-STARTPTS,loudnorm=I=-30:TP=-9:LRA=7,aresample=48000,'
        f'afade=t=in:d={fade},afade=t=out:st={seconds-fade}:d={fade}[music];'
        '[music][key]sidechaincompress=threshold=0.025:ratio=8:attack=15:release=250[duck];'
        '[voice][duck]amix=inputs=2:duration=first:normalize=0,'
        'alimiter=limit=0.89:level=false:latency=true[a]'
    )
    media.run([media.get_ffmpeg_bin(), '-v', 'error', '-y', '-i', str(source),
        '-stream_loop', '-1', '-i', str(path), '-filter_complex', graph,
        '-map', '0:v:0', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac',
        '-b:a', '192k', '-ar', '48000', '-t', str(seconds), '-movflags', '+faststart', str(output)], 240)
    def video_hash(file):
        result = subprocess.run([media.get_ffmpeg_bin(), '-v', 'error', '-i', str(file),
            '-map', '0:v:0', '-c:v', 'copy', '-f', 'hash', '-hash', 'sha256', '-'],
            capture_output=True, text=True, check=True)
        return result.stdout.strip()
    before, after = video_hash(source), video_hash(output)
    if before != after:
        raise ValueError('음악 처리 중 영상 스트림이 변경됐습니다.')
    result = subprocess.run([media.get_ffmpeg_bin(), '-hide_banner', '-i', str(output),
        '-vn', '-af', 'astats=metadata=0:reset=0', '-f', 'null', '-'],
        capture_output=True, text=True, check=True)
    peaks = [float(x) for x in re.findall(r'Peak level dB: ([-\d.]+)', result.stderr)]
    if not peaks or max(peaks) >= 0:
        raise ValueError('오디오 클리핑 검사를 통과하지 못했습니다.')
    return dict(track=track, video_stream_sha256=after, video_stream_unchanged=True,
        peak_dbfs=max(peaks), clipping_passed=True, ducking=True, fade_seconds=fade,
        listened_to_audio=False, audio_review='user_review_on_private_youtube')


def credit(description, review):
    text = review['track']['attribution']
    return description if text in description else description + '\n\nBGM: ' + text
