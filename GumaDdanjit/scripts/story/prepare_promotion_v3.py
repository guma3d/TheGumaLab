"""Create a conversational revision while preserving prior scripts and media."""
import json, shutil, sys
from pathlib import Path

CHANGES = {
    3: '여러분 주변에도 승진을 앞두고 고민이 깊어진 친구나 선배가 떠오르시나요? 축하받을 일인데, 왜 마음은 더 복잡해질까요?',
    4: '쉽게 이해가 안 되죠? 어쩌다 이런 고민이 생기는지, 조사 속 숫자부터 따라가 보겠습니다.',
    12: '그럼 한국에서는 어떤 답이 나왔을까요? 이천이십삼년 잡코리아가 엠지세대 직장인 천백십사 명에게 물었습니다.',
    24: '핸들 없이 운전하라니, 답답하죠? 결과를 책임지라면서 결과를 바꿀 수 있는 손잡이는 주지 않는 겁니다. 운전하라는데 핸들은 다른 사람이 잡고 있는 셈이죠.',
    31: '그럼 월급과 시간을 함께 놓고 계산해 볼까요? 조건을 하나 정해 보겠습니다.',
    35: '물론 성과급이나 복지, 다음 경력의 기회까지 더하면 계산은 달라집니다. 그래도 여기서 보이는 게 있죠. 월급이 오른 만큼, 내 하루도 나아졌는지는 따로 봐야 한다는 겁니다.',
    54: '하루가 이렇게 흘러간다고 생각해 보세요. 오전에는 팀 회의, 점심 뒤에는 면담, 오후에는 다른 부서와 조율. 퇴근 직전에 드디어 조용해집니다. 그제야 원래 맡던 실무를 시작합니다.',
    65: '일하는 방식이 다른 두 팀을 떠올려 보세요. 한 팀은 퇴근이 늦을수록 헌신했다고 평가합니다. 다른 팀은 같은 문제가 반복되지 않게 고쳤는지 봅니다. 어느 팀에서 어떤 행동이 늘어날지는 생각해 볼 만하죠.',
    98: '여러분 앞에 승진 제안이 두 개 놓였다고 해보죠. 직급은 같습니다. 월 보상도 같습니다.',
}

def main():
    root=Path(sys.argv[1]).resolve();parent=root.parent/'promotion-v2'
    if root.exists():raise SystemExit('Existing revision preserved; do not prepare again.')
    root.mkdir(parents=True)
    for folder in ('tools','frames','charts'): (root/folder).mkdir()
    for name in ('image-jobs.json',):
        shutil.copy2(parent/name,root/name)
    (root/'music-selection.json').write_text(json.dumps(dict(bgm_enabled=False, bgm_selection='user-request-narration-only-20261011'),indent=2),encoding='utf-8')
    # These are the scene-specific assets created for v2, never the character portraits.
    shutil.copytree(parent/'images',root/'images')
    script=json.loads((parent/'script.json').read_text(encoding='utf-8'))
    timeline=json.loads((parent/'timeline.json').read_text(encoding='utf-8'))
    edits=[];index=0
    for scene in script['scenes']:
        paragraphs=scene['narration'].split('\n\n')
        for i,text in enumerate(paragraphs):
            index+=1
            if index in CHANGES:
                paragraphs[i]=CHANGES[index];edits.append(dict(index=index,before=text,after=CHANGES[index]))
                timeline['paragraphs'][index-1]['text']=CHANGES[index]
        scene['narration']='\n\n'.join(paragraphs)
    script.update(version=6,status='draft',summary='대화체 도입과 자연스러운 예시 전환. 화면의 진행 번호·제작 안내·가상 장면 꼬리표를 제거하는 영상 v3용 대본.',
        note='2026-10-11 사용자 피드백 반영. 대본 v5·영상 v1/v2 보존. 주변에 많다는 미확인 주장은 넣지 않고 시청자의 경험을 묻는 도입. 예시의 조건은 대사 속에 자연스럽게 제시하고 조사 연도·대상·분모는 유지. 화면 제작 안내와 상세 출처는 웹 기록으로 이동. 시간표는 음성 수정 전 임시이며 완성 영상의 챕터가 실측 기준.')
    script.pop('saved_at',None)
    (root/'script.json').write_text(json.dumps(script,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'editorial-changes.json').write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'revision':3,'script':6,'paragraphs_changed':len(edits)}))

if __name__=='__main__':main()
