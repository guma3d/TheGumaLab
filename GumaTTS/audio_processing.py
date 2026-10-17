"""Measured constant-gain speech normalization, including very short utterances."""
import json
import math
import subprocess
import hashlib
from pathlib import Path


def measure(path):
    result = subprocess.run([
        'ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-vn', '-af',
        'loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json', '-f', 'null', '-'
    ], capture_output=True, text=True, check=True)
    data = json.JSONDecoder().raw_decode(result.stderr[result.stderr.rfind('{'):])[0]
    values = {'lufs': float(data['input_i']), 'true_peak_dbfs': float(data['input_tp'])}
    if not all(math.isfinite(value) for value in values.values()):
        raise RuntimeError('음성 음량을 측정할 수 없습니다. 무음 원본을 확인하세요.')
    return values


def normalize_speech(original, output, *, peak_guard=False):
    # loudnorm is measurement-only. Its one-pass dynamic gain can severely
    # attenuate short speech. A measured static gain cannot mute such a cut.
    before = measure(original)
    source = original
    guard = None
    # Native Sohee can have sparse high consonant peaks. Bound those peaks,
    # rather than lowering the whole narration below an audible music bed.
    needed = (-16.0-before['lufs']) - (-1.8-before['true_peak_dbfs'])
    if peak_guard and needed > 1:
        if needed > 8:
            raise RuntimeError('피크 보정 필요량이 너무 큽니다. 새 음성 테이크가 필요합니다.')
        ceiling = before['true_peak_dbfs']-needed
        source = Path(output).with_suffix('.peak-guard.wav')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(original),'-af',
                        f'apad=pad_dur=0.005,alimiter=limit={10**(ceiling/20):.8f}:level=false:attack=5:release=50,atrim=start=0.005,asetpts=PTS-STARTPTS',
                        '-c:a','pcm_s16le',str(source)],check=True,capture_output=True)
        guarded = measure(source)
        guard = dict(method='bounded_peak_limiter', maximum_reduction_db=round(needed,3),
                     ceiling_dbfs=round(ceiling,3), attack_ms=5, release_ms=50,
                     automatic_level=False, compensated_delay_seconds=0.005,
                     output=guarded, sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        basis = guarded
    else:
        basis = before
    gain = min(-16.0 - basis['lufs'], -1.8 - basis['true_peak_dbfs'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source),
                    '-af', f'volume={gain:.6f}dB', '-ar', '48000',
                    '-b:a', '192k', str(output)], check=True, capture_output=True)
    after = measure(output)
    expected = basis['lufs'] + gain
    if abs(after['lufs'] - expected) > 1 or after['true_peak_dbfs'] > -1:
        raise RuntimeError('음성 보정 후 음량 검증에 실패했습니다.')
    if after['lufs'] < -22:
        raise RuntimeError('음성이 너무 작습니다. 원본의 피크와 무음 구간을 검수하세요.')
    return dict(revision='bounded-peaks-static-gain-v2' if guard else 'measured-static-gain-v1', gain_db=gain, peak_guard=guard,
                input=before, output=after, expected_lufs=expected, passed=True)
