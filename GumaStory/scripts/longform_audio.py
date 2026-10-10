"""Constant-gain longform mix using measured additive true-peak headroom."""
import hashlib, json, math, subprocess
from app.core import bgm

def mix(source, output, board):
    path, track=bgm.select(board);track=dict(track)
    track['attribution']=f"{track['title']} — Kevin MacLeod (incompetech.com) · CC BY 4.0 https://creativecommons.org/licenses/by/4.0/ · 발췌·음량 조정"
    seconds=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(source)]))
    original_music=bgm.measure_audio(path,seconds,loop=True)
    mg=-25-original_music['integrated_lufs']
    music=bgm.measure_audio(path,seconds,loop=True,gain_db=mg)
    voice=bgm.measure_audio(source,seconds)
    remaining=10**(-1.5/20)-10**(music['true_peak_dbfs']/20)
    if remaining<=0:raise ValueError('Insufficient mix peak headroom')
    vg=min(-16-voice['integrated_lufs'],20*math.log10(remaining)-voice['true_peak_dbfs'])
    voice_final=bgm.measure_audio(source,seconds,gain_db=vg)
    if voice_final['integrated_lufs']-music['integrated_lufs']<6:raise ValueError('Narration/music separation below 6 LU')
    graph=f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={vg}dB[v];[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={seconds},asetpts=PTS-STARTPTS,volume={mg}dB[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-stream_loop','-1','-i',str(path),'-filter_complex',graph,'-map','0:v','-map','[a]','-map_metadata','0','-map_chapters','0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(seconds),'-movflags','+faststart',str(output)],check=True,capture_output=True)
    final=bgm.measure_audio(output,seconds)
    assert final['true_peak_dbfs']<0
    def video_hash(p):return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:v','-c:v','copy','-f','hash','-hash','sha256','-'],text=True).strip()
    before,after=video_hash(source),video_hash(output);assert before==after
    return dict(track=track,music_target_lufs=-25,music_gain_db=mg,voice_gain_db=vg,music_measurement=music,voice_measurement=voice_final,final_measurement=final,video_stream_sha256=after,video_stream_unchanged=True,clipping_passed=True,ducking=False,fade_seconds=0,music_gain_mode='constant',mix_revision='longform-measured-peak-headroom-v1',listened_to_audio=False,audio_review='user_review_on_web',speech_clarity_review='user_review_pending',pumping_review='user_review_pending')
