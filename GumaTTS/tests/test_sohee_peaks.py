import math, wave, array, shutil
from pathlib import Path
import pytest
from audio_processing import normalize_speech

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='ffmpeg required')
def test_sparse_peak_is_bounded_without_mutating_original(tmp_path):
 source=tmp_path/'speech.wav';out=tmp_path/'out.mp3';sr=24000
 samples=array.array('h',(int(32767*.08*math.sin(2*math.pi*220*i/sr)) for i in range(sr*4)))
 samples[sr*2]=int(32767*.6)
 with wave.open(str(source),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(samples.tobytes())
 original=source.read_bytes()
 proof=normalize_speech(source,out,peak_guard=True)
 assert source.read_bytes()==original
 assert proof['peak_guard']['maximum_reduction_db']<=8
 assert proof['output']['lufs']>=-18
 assert proof['output']['true_peak_dbfs']<=-1
