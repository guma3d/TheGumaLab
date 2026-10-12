"""Publish immutable keyword-free v6; reuse v5 audio resources and script v9."""
import hashlib, html, json, shutil, sys
from pathlib import Path
from story.store import Store
root=Path(sys.argv[1]);store=Store(root.parents[1])
review=json.loads((root/'production-review.json').read_text());script=json.loads((root/'script.json').read_text());timeline=json.loads((root/'timeline.json').read_text())
assert review['visual_review']=='encoded scenes, captions and numeric endpoints inspected'
assert review['logo']['failed_frames']==0 and review['audio_packet_hash_identical_to_v5']
assert review['motion']['keyword_animated_layers']==0 and review['motion']['numeric_values_and_timings_identical_to_v5']
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(root/'final.mp4')==review['video_sha256']
common=dict(character_id='',version=6,status='review',script_id='promotion',script_version=9,video_version=6,tags=['promotion','longform','video-v6','script-v9','zephyr','no-keyword-motion'])
def asset(key,path,kind,title,**fields):
    path=Path(path);target=store.root/'assets'/(key+path.suffix)
    if target.exists():assert sha(target)==sha(path)
    else:shutil.copy2(path,target)
    prior=store.asset(key)
    if prior:assert prior['sha256']==sha(path)
    else:
        item=store.add_asset(dict(common,id=key,file=target.name,kind='other' if kind=='document' else kind,title=title,tool='FFmpeg; v5 Zephyr audio unchanged',reference='promotion-film-v5',prompt='',**fields))
        if kind=='document':store.update_asset(key,item['revision'],dict(media='document'))
    return key
source=store.asset('promotion-film-v5')
poster=asset('promotion-poster-v6',root/'poster.png','other','승진 v6 표지')
reviewid=asset('promotion-v6-production-review',root/'production-review.json','document','승진 v6 · 키워드 애니메이션 제거 검수',archived=True)
captionfile=store.root/'exports/promotion-film-v6.vtt'
if captionfile.exists():assert sha(captionfile)==sha(root/'captions.vtt')
else:shutil.copy2(root/'captions.vtt',captionfile)
credits=source.get('credits','')+'\n2026-10-13 v6: 독립 키워드·헤드라인 등장/교체 및 밑줄 제거. 설명 도표는 정지 상태. 수치 카운트·막대 확장·상황 이미지 카메라 이동 유지. v5 AAC 오디오 패킷 동일, 대본·자막·BGM 그대로 재사용. v5 보존.'
videoid=asset('promotion-film-v6',root/'final.mp4','video',script['title'],width=1920,height=1080,fps=30,duration_seconds=timeline['duration'],poster_id=poster,audio_id=source['audio_id'],captions_file=captionfile.name,chapters=timeline['chapters'],parent_video_id='promotion-film-v5',cut_audio_asset_ids=source.get('cut_audio_asset_ids',[]),scene_asset_ids=source.get('scene_asset_ids',[]),bgm_enabled=True,bgm_amplitude_ratio=.5,tts_provider='gemini',tts_voice='Zephyr',tts_model='gemini-3.8-flash-tts',keyword_animation_enabled=False,credits=credits,note='키워드 애니메이션 제거 · 차트 애니메이션 유지 · 대본 v9 / v5 Zephyr 음성·자막·음악 그대로')
base='/gumaddanjit/story/media';pageid='promotion-v6-keyword-free-review'
page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>승진 · 키워드 애니메이션 제거 v6</title><style>body{{max-width:1100px;margin:36px auto;padding:0 22px;font:17px/1.8 system-ui;background:#fafaf7;color:#24343d}}video{{width:100%}}a{{color:#176c80}}</style><h1>{html.escape(script['title'])}</h1><p>영상 v6 · 대본 v9 · 22분 22초 · 1080p / 30fps</p><video controls playsinline preload="metadata" poster="{base}/{poster}/original" src="{base}/{videoid}/original"></video><p>키워드·헤드라인의 등장과 교체, 장식 밑줄을 제거했습니다. 차트 수치 카운트·막대 확장과 이미지 카메라 움직임은 유지했습니다. 설명 도표의 문항·단위·대상과 정지 비교 표기는 남겼습니다.</p><p>Zephyr 음성·요약 자막·절반 음량 배경음악은 v5 그대로이며 음성은 새로 생성하지 않았습니다. 앞으로도 독립 키워드 애니메이션은 사용하지 않습니다.</p><p><a href="/gumaddanjit/story/watch/{videoid}">영상 보관함</a> · <a href="{base}/{videoid}/original">MP4 원본</a> · <a href="{base}/promotion-v5-script-and-captions/original">대본과 요약 자막</a> · <a href="{base}/{reviewid}/original">검수 기록</a> · <a href="{base}/promotion-v5-motion-review/original">이전 v5</a></p><p>Carefree — Kevin MacLeod (incompetech.com) · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> · 발췌·음량 조정</p></html>'''
(root/'review.html').write_text(page,encoding='utf-8');asset(pageid,root/'review.html','document','승진 v6 · 키워드 애니메이션 제거',archived=True)
pub=dict(video_id=videoid,url=f'https://home.guma3d.com{base}/{pageid}/original',video_url=f'https://home.guma3d.com/gumaddanjit/story/watch/{videoid}',video_sha256=review['video_sha256'],script_version=9,video_version=6,parent_version=5)
(root/'publication.json').write_text(json.dumps(pub,ensure_ascii=False,indent=2));print(json.dumps(pub,ensure_ascii=False))
