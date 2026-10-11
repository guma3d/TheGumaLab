"""Publish checked visual revision and every generated scene without overwriting v1."""
import hashlib,json,shutil,sys
from pathlib import Path
from PIL import Image

root=Path(sys.argv[1]).resolve();storage=root.parents[1]
review=json.loads((root/'production-review.json').read_text())
assert review['audio_stream_unchanged'] and review['logo']['failed_frames']==0
assert review['technical_review']['encoded_contact_sheets']==6
assert review['visual_review']=='all 114 encoded midpoint frames and full-size numeric-caption samples inspected'
script=json.loads((root/'script.json').read_text());timeline=json.loads((root/'timeline.json').read_text())
jobs=json.loads((root/'image-jobs.json').read_text());prompts={j['index']:j for j in json.loads((root/'generation-prompts.json').read_text())}
corrections={j['index']:j for j in json.loads((root/'generation-corrections.json').read_text())}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(root/'final.mp4')==review['video_sha256'], 'Video changed after review'
assert sha(root/'script.json')==review['script_sha256'], 'Script changed after review'
assert len(jobs)==65 and len({sha(root/j['file']) for j in jobs})==65
for j in jobs:assert sha(root/j['file'])==j['sha256'], 'Scene changed after visual review'
def preserve(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert sha(src)==sha(dst),f'Immutable asset differs: {dst}'
    else:shutil.copy2(src,dst)
def record(item):
    target=storage/'imports'/(item['id']+'.json');text=json.dumps(item,ensure_ascii=False,indent=2)
    if target.exists():assert target.read_text(encoding='utf-8')==text
    else:target.write_text(text,encoding='utf-8')
common=dict(character_id='',version=2,status='review',tags=['promotion','longform','video-v2','script-v5'])
for j in jobs:
    aid=f'promotion-v2-scene-{j["index"]:03}';file=aid+'.png';preserve(root/j['file'],storage/'assets'/file)
    references=[dict(id=r,sha256=sha(storage/'assets'/(r+'.png'))) for r in j['reference_ids']]
    prompt=prompts[j['index']]['prompt']
    if j['index'] in corrections:prompt+='\n\nFinal correction / regeneration:\n'+corrections[j['index']]['prompt']
    record(dict(common,id=aid,file=file,kind='scene',title=f'승진 v2 · CUT {j["index"]:03} · {j["headline"]}',
       tool='built-in ImageGen',reference=', '.join(j['reference_ids']),prompt=prompt,reference_hashes=references,
       edit_lineage=corrections.get(j['index'],{}),
       script_id='promotion',script_version=5,video_version=2,scene=j['scene'],paragraph=j['paragraph'],
       note='레퍼런스를 얼굴·체형·의상·스타일 입력으로 사용해 새로 생성한 해당 대사 전용 상황 컷. 설명용 가상 장면. 생성과 검수는 사용자 최종 승인과 구분합니다.',
       narration=j['narration']))
preserve(root/'final.mp4',storage/'assets/promotion-film-v2.mp4')
preserve(root/'captions.vtt',storage/'exports/promotion-film-v2.vtt')
poster=root/'poster.png'
if not poster.exists():
    im=Image.open(root/'frames/001.png').convert('RGBA');im.alpha_composite(Image.open(root/'logo-layer.png').convert('RGBA'));im.convert('RGB').save(poster)
preserve(poster,storage/'assets/promotion-poster-v2.png')
record(dict(common,id='promotion-poster-v2',file='promotion-poster-v2.png',kind='other',title='승진 · 영상 v2 표지',tool='ImageGen scene + editorial composition',reference='promotion-v2-scene-001',prompt='새 도입 장면에 승인된 GumaStory 로고 합성.',note='영상 v2 첫 장면.'))
parent=json.loads((storage/'imports/promotion-film-v1.json').read_text())
credits='\n'.join([
 '대본: promotion v5 · 영상 v2 · 부모 영상: promotion-film-v1',
 '수정: 65개 상황 컷을 내장 ImageGen으로 각각 새로 생성. 기존 레퍼런스 원본을 영상 컷으로 직접 사용하지 않음.',
 '캐릭터 기준: adult-man-01 / adult-woman-01-v3. 컷별 참조·프롬프트·교정·해시는 리소스 보관함과 제작 원본에 보존.',
 '자막: Pretendard SemiBold 46px · 얇은 단일 외곽선 1.3px · 이중 테두리/팝 확대 제거 · 최대 2줄.',
 '표시 원고: 수치·금액·인원·연도·시간을 숫자로 표기. 승인 대본과 낭독 파일은 변경하지 않음.',
 '음성·배경음악: v1의 기존 믹스를 재인코딩 없이 재사용했으며 전체 압축 오디오 해시 일치 확인. 신규 TTS 생성 없음.',
 '자막 타이밍: 원본 문단 경계 기준, 문단 안은 읽기 길이에 따른 추정. 실제 전편 청취 검수는 미완료.',
 '검수: 114개 완성 화면, 숫자 자막, 12개 챕터, 전체 프레임 로고 검사.',
 '제작 원본: D:\\TheGumaLab\\GumaDdanjit\\storage\\story\\productions\\promotion-v2',
 '최종 MP4: storage/story/assets/promotion-film-v2.mp4',
 '프롬프트: productions/promotion-v2/generation-prompts.json 및 generation-corrections.json',
 '원 대본의 자료·음원 출처:\n국내 조사:'+parent['credits'].split('국내 조사:',1)[1].split('음성: Zephyr',1)[0]
])
film=dict(common,id='promotion-film-v2',file='promotion-film-v2.mp4',kind='video',title=script['title'],tool='built-in ImageGen + FFmpeg/Pillow; unchanged v1 audio',
    reference='promotion-film-v1; promotion script v5; 65 new scene assets',prompt='2026-10-11 사용자 피드백: 얇고 읽기 쉬운 자막, 숫자 표시, 레퍼런스를 활용한 새로운 장면별 이미지.',
    script_id='promotion',script_version=5,video_version=2,parent_video_id='promotion-film-v1',width=1920,height=1080,fps=30,duration_seconds=timeline['duration'],
    poster_id='promotion-poster-v2',audio_id='promotion-narration-v1',captions_file='promotion-film-v2.vtt',chapters=timeline['chapters'],credits=credits,
    scene_asset_ids=[f'promotion-v2-scene-{j["index"]:03}' for j in jobs],
    note='영상 v2 · 새 상황 이미지 65컷으로 교체하고, 자막을 Pretendard와 얇은 단일 테두리로 바꿨습니다. 6%, 54.8%, 400만 원처럼 화면용 숫자 표기를 적용했습니다. 기존 대본·음성·음악은 유지했습니다. v1 및 원본·교정 이력은 보존됩니다.')
record(film)
print(json.dumps({'video':film['id'],'images':len(jobs),'bytes':(root/'final.mp4').stat().st_size}))
