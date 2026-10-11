"""Save immutable script metadata matching the measured v3 narration timeline."""
import hashlib,json,shutil,sys
from pathlib import Path
from story.store import Store
root=Path(sys.argv[1]);script=json.loads((root/'script.json').read_text());timeline=json.loads((root/'timeline.json').read_text());plan=json.loads((root/'visual-plan.json').read_text())
if script.get('timing_basis')=='measured_cut_audio':raise SystemExit('Final script metadata already saved.')
assert script['version']>=6
preserved=root/f'script-v{script["version"]}-before-retiming.json'
if not preserved.exists():shutil.copy2(root/'script.json',preserved)
for scene,chapter in zip(script['scenes'],timeline['chapters']):
    scene['start']=round(chapter['start']);scene['end']=round(chapter['end'])
    cuts=[p for p in plan if p['scene']==chapter['scene']]
    scene['asset_ids']=list(dict.fromkeys(p['image_id'] for p in cuts if p['image_id']))
    scene['asset_ids'].extend(f'promotion-v3-voice-{p["index"]:03}' for p in cuts)
    scene['visual']='대사에 맞춘 상황 이미지·데이터 차트·설명 화면. 진행 번호와 제작 안내 꼬리표를 제거하고 GumaStory 로고·얇은 숫자 자막을 적용. 컷별 로컬 남성 M5 음성, 배경음악 없음. 장면별 원본·참조·출처·검수 기록은 제작 보관함 참조.'
script.update(timing_basis='measured_cut_audio',summary='자연스러운 질문으로 시작하는 승진 이야기. 컷별 로컬 M5 내레이션, 배경음악과 화면 제작 안내 제거. 완성 음성 기준 시간표.',note='2026-10-11 피드백 반영 영상 v3의 실측 시간표와 실제 장면 리소스. 발음 표기를 정리한 대본의 낭독 문장은 유지하고 화면 제작 지시·음성·음악·시간표 메타데이터를 갱신. 실제 조사와 예시 조건은 내용·출처에서 구분하며 상세 제작 이력은 웹 보존. 이전 대본·영상·원본·실패 테이크 보존.')
saved=Store(root.parents[1]).save_script('promotion',script['version'],script)
(root/'script.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
review=json.loads((root/'production-review.json').read_text());review.update(script_version=saved['version'],script_sha256=hashlib.sha256((root/'script.json').read_bytes()).hexdigest())
(root/'production-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'script_version':saved['version'],'duration':timeline['duration']}))
