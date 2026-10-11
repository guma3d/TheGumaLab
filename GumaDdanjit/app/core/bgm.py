"""Verified music library, narration-first mixing and lossless video preservation."""
import hashlib
import json
import math
import secrets
import re
import subprocess
from pathlib import Path
from app.config import STORAGE_DIR
from app.core import official_clips as media

TRACK_TITLES = ('Life of Riley', 'Carefree', 'Monkeys Spinning Monkeys', 'Wallpaper', 'Fluffing a Duck')
LEGACY_TRACK_TITLES = ('Raising Me Higher', 'Curiosity', "I'm Fine", 'Break Away', 'The King')
MIXKIT_LICENSE = 'Mixkit Stock Music Free License'
MUSIC_LUFS = -25.0
VOICE_LUFS = -16.0


def assign_random(board):
    """Draw once per new video; persist the result for retries and credits."""
    for title in TRACK_TITLES:
        select({'bgm_track': title})
    board['bgm_track'] = secrets.choice(TRACK_TITLES)
    board['bgm_selection'] = 'random-five-kevin-compact-credit-v3'
    return select(board)


def select(board):
    library = STORAGE_DIR / 'audio' / 'bgm'
    tracks = json.loads((library / 'manifest.json').read_text(encoding='utf-8-sig'))
    title = board.get('bgm_track')
    if not title:
        return assign_random(board)
    if title not in TRACK_TITLES + LEGACY_TRACK_TITLES:
        raise ValueError('검증된 BGM 목록에 없는 곡입니다.')
    track = next((t for t in tracks if t['title'] == title), None)
    if not track:
        raise ValueError('검증된 BGM 목록에 없는 곡입니다.')
    path = (library / track['filename']).resolve()
    if path.parent != library.resolve() or not path.is_file():
        raise ValueError('BGM 원본이 없습니다.')
    if hashlib.sha256(path.read_bytes()).hexdigest().lower() != track['sha256'].lower():
        raise ValueError('BGM 원본 해시가 다릅니다.')
    if not valid_license(track):
        raise ValueError('BGM 이용 근거와 크레딧이 필요합니다.')
    return path, track


def valid_license(track):
    if track.get('license') == 'CC BY 4.0':
        return bool(track.get('attribution'))
    return (track.get('license') == MIXKIT_LICENSE
        and track.get('attribution_required') is False
        and track.get('license_url') == 'https://mixkit.co/license/#musicFree'
        and track.get('attribution_policy_url') == 'https://mixkit.co/free-stock-music/'
        and bool(track.get('license_checked_at')))


def has_required_credit(description, review):
    track = review['track']
    return valid_license(track) and (track.get('license') == MIXKIT_LICENSE
        or track['attribution'] in description)


def measure_audio(path, seconds, *, loop=False, gain_db=0.0):
    """Measure the exact stereo segment; loudnorm is analysis only, never the mix."""
    args = [media.get_ffmpeg_bin(), '-hide_banner', '-nostats']
    if loop:
        args += ['-stream_loop', '-1']
    args += ['-i', str(path), '-vn', '-af',
        f'aresample=48000,aformat=channel_layouts=stereo,atrim=duration={seconds},'
        f'asetpts=PTS-STARTPTS,volume={gain_db}dB,'
        'loudnorm=I=-16:TP=-1:LRA=11:print_format=json',
        '-t', str(seconds), '-f', 'null', '-']
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    data = json.JSONDecoder().raw_decode(result.stderr[result.stderr.rfind('{'):])[0]
    measured = dict(integrated_lufs=float(data['input_i']), true_peak_dbfs=float(data['input_tp']))
    if not all(math.isfinite(v) for v in measured.values()):
        raise ValueError('음량을 측정할 수 없는 무음 또는 손상된 소스입니다.')
    return measured


def mix(source, output, board):
    path, track = select(board)
    track = dict(track)
    if track.get('license') == 'CC BY 4.0' and track.get('artist') == 'Kevin MacLeod':
        track['attribution'] = (f"{track['title']} — Kevin MacLeod (incompetech.com) · "
            'CC BY 4.0 https://creativecommons.org/licenses/by/4.0/ · 발췌·음량 조정')
    else:
        track['attribution'] = track.get('attribution', '').replace('·페이드', '')
    seconds = media.duration(source)
    original_music = measure_audio(path, seconds, loop=True)
    music_gain = MUSIC_LUFS - original_music['integrated_lufs']
    music_level = measure_audio(path, seconds, loop=True, gain_db=music_gain)
    if abs(music_level['integrated_lufs'] - MUSIC_LUFS) > .3:
        raise ValueError('BGM 구간 음량이 공통 기준과 다릅니다.')
    original_voice = measure_audio(source, seconds)
    # Reserve additive peak headroom by changing narration gain once, not music
    # in response to speech. No limiter, compressor, fade or dynamic loudnorm.
    remaining_peak = 10 ** (-1 / 20) - 10 ** (music_level['true_peak_dbfs'] / 20)
    if remaining_peak <= 0:
        raise ValueError('음악 피크에 안전한 믹싱 여유가 없습니다.')
    voice_peak_ceiling = min(-5.0, 20 * math.log10(remaining_peak))
    voice_gain = min(VOICE_LUFS - original_voice['integrated_lufs'],
        voice_peak_ceiling - original_voice['true_peak_dbfs'])
    voice_level = measure_audio(source, seconds, gain_db=voice_gain)
    if voice_level['integrated_lufs'] - music_level['integrated_lufs'] < 6:
        raise ValueError('대사와 BGM 음량 차이가 부족합니다. 음성 원본을 검수하세요.')
    graph = (
        f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={voice_gain}dB[voice];'
        f'[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={seconds},'
        f'asetpts=PTS-STARTPTS,volume={music_gain}dB[music];'
        '[voice][music]amix=inputs=2:duration=first:normalize=0[a]'
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
    final_level = measure_audio(output, seconds)
    if final_level['true_peak_dbfs'] >= 0:
        raise ValueError('최종 오디오 true-peak 검사를 통과하지 못했습니다.')
    return dict(track=track, video_stream_sha256=after, video_stream_unchanged=True,
        peak_dbfs=max(peaks), clipping_passed=True, ducking=False, fade_seconds=0,
        music_target_lufs=MUSIC_LUFS, music_gain_db=music_gain,
        voice_gain_db=voice_gain, music_measurement=music_level, voice_measurement=voice_level,
        final_measurement=final_level, music_gain_mode='constant',
        mix_revision='constant-normalized-bgm-v3',
        listened_to_audio=False, audio_review='user_review_on_web',
        speech_clarity_review='user_review_pending', pumping_review='user_review_pending')


def credit(description, review):
    if not valid_license(review['track']):
        raise ValueError('BGM 이용 근거와 크레딧이 필요합니다.')
    if review['track']['license'] == MIXKIT_LICENSE:
        return description
    text = review['track']['attribution']
    return description if text in description else description + '\n\nBGM: ' + text
