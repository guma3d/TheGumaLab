"""Publish the reviewed narration-only revision while preserving earlier media."""
import hashlib,json,shutil,sys
from pathlib import Path
from PIL import Image
root=Path(sys.argv[1]).resolve();storage=root.parents[1]
review=json.loads((root/'production-review.json').read_text());timeline=json.loads((root/'timeline.json').read_text());script=json.loads((root/'script.json').read_text())
assert review['bgm_enabled'] is False and review['technical_review']['no_bgm_verified']
assert review['logo']['failed_frames']==0 and review['technical_review']['audio_cuts_checked']==114
assert review['visual_review']=='114 unchanged scene frames verified against inspected render; all final caption strips and full-size numeric captions inspected'
assert review['asr_review']['cut_count']==114 and review['asr_review']['meaningful_mismatches']==0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/'final.mp4')==review['video_sha256'] and sha(root/'script.json')==review['script_sha256']
def preserve(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert sha(src)==sha(dst),'Immutable asset differs'
    else:shutil.copy2(src,dst)
def record(item):
    p=storage/'imports'/(item['id']+'.json');text=json.dumps(item,ensure_ascii=False,indent=2)
    if p.exists():assert p.read_text(encoding='utf-8')==text
    else:p.write_text(text,encoding='utf-8')
common=dict(character_id='',version=3,status='review',script_id='promotion',script_version=script['version'],video_version=3,tags=['promotion','longform','video-v3',f'script-v{script["version"]}'])
voices=json.loads((root/'voice-manifest.json').read_text());checks=json.loads((root/'cut-audio-review.json').read_text())
for voice,check in zip(voices,checks):
    aid=f'promotion-v3-voice-{voice["index"]:03}';file=aid+'.mp3';source=root/voice['file']
    assert sha(source)==voice['audio_sha256'] and voice['index']==check['index']
    preserve(source,storage/'assets'/file)
    meta=json.loads(source.with_suffix('.tts.json').read_text())
    record(dict(common,id=aid,file=file,kind='audio',title=f'승진 v3 · CUT {voice["index"]:03} · M5 음성',tool='GumaTTS local Qwen3-TTS VoiceDesign M5',reference=meta['web_url'],prompt=voice['text'],narration=voice['text'],cut_index=voice['index'],scene=voice['scene'],text_sha256=voice['text_sha256'],tts_job_id=voice['tts_job_id'],tts_provenance=meta,audio_review=check,duration_seconds=voice['duration'],note='컷별 재사용 음성. 동일 원문·모델·프로필의 정상 컷은 다음 편집에서 재생성하지 않습니다. 원본 WAV·이전 테이크는 제작 폴더와 GumaTTS 작업실에 보존. 실제 청취·사용자 승인은 별도입니다.'))
preserve(root/'final.mp4',storage/'assets/promotion-film-v3.mp4')
preserve(root/'captions.vtt',storage/'exports/promotion-film-v3.vtt')
preserve(root/'narration-master.mp3',storage/'assets/promotion-narration-v3.mp3')
record(dict(common,id='promotion-narration-v3',file='promotion-narration-v3.mp3',kind='audio',title='승진 v3 · 로컬 M5 내레이션',tool='GumaTTS Qwen3-TTS 1.7B VoiceDesign M5',reference='114 individually archived local M5 cuts',prompt='확정된 남성 M5로 컷별 생성 후 연결. 정상 컷 재사용, BGM 없음, 피치·배속 변경 없음.',note='로컬 생성. 컷별 원문·모델·작업 ID·원본/보정/최종 해시와 검수 기록 보존. 실제 청취와 사용자 승인은 별도.',duration_seconds=timeline['duration']))
poster=root/'poster.png'
if not poster.exists():
    im=Image.open(root/'frames/001.png').convert('RGBA');im.alpha_composite(Image.open(root/'logo-layer.png').convert('RGBA'));im.convert('RGB').save(poster)
preserve(poster,storage/'assets/promotion-poster-v3.png')
record(dict(common,id='promotion-poster-v3',file='promotion-poster-v3.png',kind='other',title='승진 · 영상 v3 표지',tool='ImageGen scene + composition',reference='promotion-v2-scene-001',prompt='도입 상황 컷에 GumaStory 로고를 합성.',note='새 자막·안내문구 정리 버전의 표지.'))
charts=json.loads((root/'chart-provenance.json').read_text())
for i,chart in enumerate(charts,1):
    aid=f'promotion-v3-chart-{i:02}';preserve(root/f'charts/{i:02}.png',storage/'assets'/(aid+'.png'))
    record(dict(common,id=aid,file=aid+'.png',kind='other',title=f'승진 v3 · 차트 {i}',tool='Pillow data-native chart',reference='promotion-v4 verified chart data',prompt='검증된 수치 유지, 진행 번호·제작 안내문구 제거. 상세 출처는 웹 보존.',note=json.dumps(chart,ensure_ascii=False),provenance=chart))
parent=json.loads((storage/'imports/promotion-film-v2.json').read_text())
source_credits=parent['credits'].split('원 대본의 자료·음원 출처:',1)[-1]
credits='\n'.join([
 f'대본 promotion v{script["version"]} · 영상 v3 · 부모 영상 promotion-film-v2',
 '2026-10-11 사용자 피드백: 가상 장면 대사를 자연스러운 질문·예시 조건으로 수정. 진행 번호·가상/설명용/편집자 화면 안내 제거.',
 '음성: 로컬 Qwen3-TTS 1.7B VoiceDesign · 선정된 남성 M5 · GumaTTS 경유. 114컷 별도 저장·연결. 수정되지 않은 정상 컷은 다음 버전에서 재사용.',
 '배경음악: 없음. 깨끗한 내레이션 원본에서 출력했으며 모든 최종 컷의 음성 파형 대조로 확인.',
 '자막: Pretendard SemiBold 46px, 단일 1.3px 외곽선, 최대 2줄, 수치 숫자 표시. 컷별 음성 경계 기준, 컷 내부는 읽기 길이 추정.',
 '이미지: v2에서 캐릭터 레퍼런스를 입력으로 새로 생성·검수한 65개의 장면별 이미지 유지. 초상 레퍼런스를 영상으로 직접 사용하지 않음.',
 '검수: 컷별 원본·보정·최종 음량/피크, 자동 전사 대사 대조, 모든 프레임 로고, 114개 완성 장면·수치 자막. 실제 전편 청취·사용자 승인은 미완료.',
 '기존 v1/v2와 원본·실패 테이크·프롬프트·참조 해시·출처·검수는 보존.',
 '제작 원본: storage/story/productions/promotion-v3',source_credits])
film=dict(common,id='promotion-film-v3',file='promotion-film-v3.mp4',kind='video',title=script['title'],tool='GumaTTS local M5 + ImageGen scene assets + FFmpeg/Pillow',
    reference=f'promotion-film-v2; promotion script v{script["version"]}; local per-cut M5 narration',prompt='자연스러운 도입, 화면 제작 안내·진행 번호 제거, 배경음악 없이 로컬 남성 M5 컷별 음성 연결.',
    script_id='promotion',script_version=script['version'],video_version=3,parent_video_id='promotion-film-v2',width=1920,height=1080,fps=30,duration_seconds=timeline['duration'],poster_id='promotion-poster-v3',audio_id='promotion-narration-v3',captions_file='promotion-film-v3.vtt',chapters=timeline['chapters'],credits=credits,
    scene_asset_ids=parent['scene_asset_ids'],chart_asset_ids=[f'promotion-v3-chart-{i:02}' for i in range(1,6)],cut_audio_asset_ids=[f'promotion-v3-voice-{v["index"]:03}' for v in voices],bgm_enabled=False,tts_voice='M5',tts_provider='local',
    note='영상 v3 · 대화 흐름을 끊던 제작 안내 대사를 수정하고 화면의 번호·가상/설명용 안내를 제거했습니다. 배경음악 없이 로컬 남성 M5를 114컷별로 생성·보관·연결했습니다. 숫자 자막과 장면별 이미지, 이전 버전은 유지·보존합니다.')
record(film)
print(json.dumps({'video':film['id'],'bgm_enabled':False,'duration':timeline['duration']}))
