import shutil
import subprocess
import pytest
from audio_processing import normalize_speech


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='ffmpeg required')
@pytest.mark.parametrize('seconds', [0.5, 1.4, 2.5, 3.0, 5.0])
def test_short_audio_preserves_measured_gain(tmp_path, seconds):
    source, output = tmp_path/'source.wav', tmp_path/'audio.mp3'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                    f'sine=frequency=700:duration={seconds}', str(source)], check=True)
    proof = normalize_speech(source, output)
    assert abs(proof['output']['lufs'] - proof['expected_lufs']) < 1
    assert proof['output']['lufs'] >= -22


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='ffmpeg required')
def test_silent_source_is_rejected(tmp_path):
    source = tmp_path/'silent.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                    'anullsrc=r=24000:cl=mono', '-t', '2', str(source)], check=True)
    with pytest.raises(RuntimeError, match='무음'):
        normalize_speech(source, tmp_path/'audio.mp3')
