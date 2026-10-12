# 쇼핑쇼츠 고정 음성 운영 기준

2026-10-11 사용자 최종 채택. Food·Tech·Living 대상이며 Story 롱폼의 컷별 M5 방식과 다르다.

- 모델: GumaTTS qwen-clone-1.7b, Qwen3-TTS 1.7B Base Voice Clone.
- 참조: GumaTTS/storage/fixed-voices/F4-dates-v1/reference.wav와 reference.json의 대본. 최초 로컬 F4 대추야자 v5 CUT7 원본이며 생성물을 다시 복제하지 않는다.
- WAV SHA256: c5c7d003d5292bbe7e0d66dd7b3ebae8e471f9643084529b48928765b96c93ef. 요청 전 실제 WAV·참조 대본 해시를 확인한다.
- 전체 승인 대사를 한 요청으로 생성하고 작업 ID·실제 모델·설정·원본 WAV·보정 음성·마스터 해시를 보존한다. Base가 지원하지 않는 style/instruct, 피치/배속 변경은 사용하지 않는다.
- ASR 발화 경계와 원문을 대조해 컷·자막 타임라인을 맞춘다. 컷별 파생 파일은 정렬/검수용이며 최종 음성은 분할 재접합하지 않은 연속 마스터다.
- 추가 발화·누락·무음·잘림·발음 의심·클리핑·컷별 음량·BGM 대비를 검사한다. 숫자 표기/낭독 차이는 근거 있게 정규화하고 자동 검사와 실제 청취를 구분한다. 최종 모든 프레임의 로고·움직임·전환·제품 외형도 확인한다.
- 수정 범위 밖 소스·대본·사용자 평가·선택 BGM/고정 게인·썸네일을 보존한다. 기존 공개 영상을 정책 채택만으로 바꾸지 않는다. 정확한 버전의 제작/업로드/공개 요청 범위를 따른다.

검증된 운영 경로는 [전체 단일 생성 인계](../storage/shorts/handoffs/shopping-f4-single-pass-20261011/REPORT.md), [대추야자 생성·정렬·검수](../storage/shorts/handoffs/dates-f4-single-pass-20261011/REPORT.md) 및 각 폴더의 generate.py / produce.py / render.py / audit.py다. 과거 승인 도구를 다른 아이템에 그대로 실행하지 말고 입력·참조·승인 범위·새 출력 버전을 준비한다.

shopping.py 컷별 자동 제작과 tts_engine.py의 F1-bright-v2는 과거 실행 경로다. 새 쇼핑 제작에 사용하지 않는다. 문서/JSON 최신화는 자동 렌더러 전체 개편을 뜻하지 않는다. 단일 생성 인계 방식으로 제작하고 실제 요청/마스터/최종 음성을 대조한다.

[food-f4-20261011.md](food-f4-20261011.md)는 앞선 v5/v4/v6 컷별 VoiceDesign 교체 **이력**이며 현재 기본 생성 지침이 아니다.
