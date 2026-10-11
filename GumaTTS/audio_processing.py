"""Measured constant-gain speech normalization, including very short utterances."""
import json
import math
import subprocess


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


def normalize_speech(original, output):
    # loudnorm is measurement-only. Its one-pass dynamic gain can severely
    # attenuate short speech. A measured static gain cannot mute such a cut.
    before = measure(original)
    gain = min(-16.0 - before['lufs'], -1.8 - before['true_peak_dbfs'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(original),
                    '-af', f'volume={gain:.6f}dB', '-ar', '48000',
                    '-b:a', '192k', str(output)], check=True, capture_output=True)
    after = measure(output)
    expected = before['lufs'] + gain
    if abs(after['lufs'] - expected) > 1 or after['true_peak_dbfs'] > -1:
        raise RuntimeError('음성 보정 후 음량 검증에 실패했습니다.')
    if after['lufs'] < -22:
        raise RuntimeError('음성이 너무 작습니다. 원본의 피크와 무음 구간을 검수하세요.')
    return dict(revision='measured-static-gain-v1', gain_db=gain,
                input=before, output=after, expected_lufs=expected, passed=True)
