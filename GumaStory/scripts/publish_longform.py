"""Publish immutable local production files to GumaStory's authenticated library."""
import hashlib, json, shutil, sys
from pathlib import Path

source=Path(sys.argv[1]).resolve()
storage=Path(__file__).resolve().parents[1]/'storage'
review=json.loads((source/'production-review.json').read_text(encoding='utf-8'))
timeline=json.loads((source/'timeline.json').read_text(encoding='utf-8'))
script=json.loads((source/'script.json').read_text(encoding='utf-8'))
assert script['id']=='promotion' and script['version']==5
assert review['clipping_passed'] and review['video_stream_unchanged']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def preserve(src,dst):
    dst.parent.mkdir(exist_ok=True,parents=True)
    if dst.exists():
        assert sha(src)==sha(dst),f'Immutable destination differs: {dst.name}'
    else:shutil.copy2(src,dst)
archive=storage/'productions'/'promotion-v1'
for src in source.rglob('*'):
    if src.is_file():preserve(src,archive/src.relative_to(source))
for src,name in [('final.mp4','promotion-film-v1.mp4'),('narration.mp3','promotion-narration-v1.mp3'),('frames/001.png','promotion-poster-v1.png')]:
    preserve(source/src,storage/'assets'/name)
preserve(source/'captions.vtt',storage/'exports'/'promotion-film-v1.vtt')
shared=dict(character_id='',version=1,status='review',tool='Gemini Zephyr TTS + FFmpeg/Pillow editing',reference='promotion script v5; production archive storage/productions/promotion-v1',prompt='사용자가 승인한 v5 원문. 기존 승인 캐릭터·차트, 문단별 TTS, 고정 화면 편집, 한국어 자막, 출처 표기. 원문과 원본 보존.',tags=['promotion','longform','video-v1','script-v5'])
audio=dict(shared,id='promotion-narration-v1',file='promotion-narration-v1.mp3',kind='audio',title='승진 · 내레이션 v1 (대본 v5)',note='Zephyr 음성. 원문 문단별 생성 후 앞뒤 무음을 정리하고 전체 템포를 조정. 실제 청취 검수는 웹에서 확인 필요.')
poster=dict(shared,id='promotion-poster-v1',file='promotion-poster-v1.png',kind='other',title='승진 · 영상 v1 표지',note='승인된 지하철 일러스트로 편집한 첫 화면. 새로운 캐릭터 생성 없음.')
credits='\n'.join(['대본: promotion v5 · 사용자 제작 승인 2026-10-10',
    '국내 조사: 잡코리아, 2023-05-12 발표 · MZ 직장인 1,114명',
    'https://www.jobkorea.co.kr/goodjob/tip/view?News_No=21013',
    '글로벌 조사: Deloitte 2026 · 44개국 · Gen Z 14,384명',
    'https://www.deloitte.com/global/en/about/press-room/deloitte-2026-gen-z-and-millennial-survey.html',
    '역할 적합성 연구: Benson·Li·Shue (2019), QJE · 미국 131개 기업',
    'https://doi.org/10.1093/qje/qjz022',
    '국내·해외·연도·문항은 구분. 가상 계산과 업무 장면은 실제 통계·인터뷰가 아님.',
    'BGM: '+review['track']['attribution'],
    '음성: Zephyr · 화면: 기존 ImageGen 일러스트 + 직접 제작한 차트·표 · 자막: 메이플스토리 Bold',
    '음성 모델 기록: '+', '.join(review.get('tts_models',[])),
    '기술 검증: 영상/음성 스트림, 클리핑, BGM 고정 음량, 데이터 출처, 버전·해시 보존. 실제 전편 청취 검수는 미완료.'])
film=dict(shared,id='promotion-film-v1',file='promotion-film-v1.mp4',kind='video',title=script['title'],
    script_id='promotion',script_version=5,video_version=1,width=1920,height=1080,fps=30,duration_seconds=timeline['duration'],
    poster_id=poster['id'],audio_id=audio['id'],captions_file='promotion-film-v1.vtt',chapters=timeline['chapters'],credits=credits,
    note='영상 v1 · 대본 v5 기준. 일러스트·차트형 해설 영상에 내레이션·배경음악·한국어 자막을 넣었습니다. 아래 구간을 누르면 해당 장면으로 이동합니다. 기술 검사 완료, 실제 전편 청취 검수는 남아 있습니다. 문단 안 자막 타이밍은 읽기 길이로 추정해 일부 오차가 있을 수 있습니다. YouTube 게시본이 아닌 웹 검토본입니다.')
for item in [audio,poster,film]:
    target=storage/'imports'/(item['id']+'.json')
    value=json.dumps(item,ensure_ascii=False,indent=2)
    if target.exists():assert target.read_text(encoding='utf-8')==value
    else:target.write_text(value,encoding='utf-8')
print(json.dumps({'video':'promotion-film-v1','seconds':timeline['duration'],'bytes':(storage/'assets'/film['file']).stat().st_size,'archive':str(archive)},ensure_ascii=False))
