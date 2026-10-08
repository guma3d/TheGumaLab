# Main 이어받기 — 2026-10-08

이 파일은 큰 이미지 이력을 복제하지 않고 Main 업무를 이어받기 위한 요약이다. 원본 대화와 제작 파일은 보존한다. 시점이 지난 상태는 실제 파일·웹에서 다시 확인한다.

## 환경과 기준 문서

- HomeServer Guma3D, 작업 디렉터리 `D:\TheGumaLab`, 저장소 `guma3d/TheGumaLab`, 기본 main. SSH origin과 상위 AGENTS.md의 커밋·동기화 지침을 따른다.
- 현재 Main: `01a10a44-3943-7d62-8798-5295f8100402`. 아직 대체 세션을 만들지 않았다.
- 제작 정책: `GumaVideoFactory/AGENTS.md`, `RESEARCH.md`, `README.md`, `app/core/production_rules.json`. Food/Tech/Living 역할·주소는 README가 기준이다.
- 한국어로 답한다. 비밀값은 출력·커밋하지 않는다. 파일과 웹의 버전 기록을 우선 사용하고 이전 전체 대화·이미지를 다시 불러오지 않는다.

## 지속되는 사용자 승인 원칙

- 원본·수정본·최종본 모두 프로젝트 storage에 로컬 보존하고 웹에서 버전별 검토한다.
- 최종본이 완성되어도 사용자가 정확한 버전을 업로드 요청한 때만 YouTube에 업로드한다. 공개 승인은 별개다. 고급 기능 승인이 업로드·공개 승인을 뜻하지 않는다.
- 모든 신규 영상은 Food 승인 Zephyr 음성. 검증한 5곡 중 1곡을 무작위 선택하고 재시도에서는 같은 곡을 유지한다. BGM -25 LUFS 고정 음량, 대사 연동 감쇠·페이드 없음. 상세 수치는 RESEARCH.md를 따른다.
- 피드백은 관련 최신 MD와 실행 규칙에 반영하고 오래된 규칙을 정리한다. 버전별 과거 원본·검수 이력은 보존한다.

## 최근 확인한 결과

- 2026-10-08 이 대화에서 GumaShop 채널 `UCRtAVFQFmJCcpvLeuyq03Kg`의 YouTube Studio → Settings → Channel → Feature eligibility를 직접 확인했다. Advanced features가 Pending에서 **Enabled**로 바뀌었다. Standard/Intermediate도 Enabled였다.
- 흑임자인절미찰떡아이스 아이템 `dadc1759bf7912ef`: Video v0002, Preview v0003 웹 검토본 완료. 사용자 최종 공개 승인 없음. 새로운 요청 없이 재제작·업로드하지 않는다.
- 검토 링크: https://videofactory.guma3d.com/ideas/dadc1759bf7912ef#Video
- 파일: `D:\TheGumaLab\GumaVideoFactory\storage\products\dadc1759bf7912ef\Video\v0002\final.mp4`
- SHA256: `e98fd07d47ec527399bba4a0c5b95c83455e9f0066134356b24b8387510f90d1`, 41초, 1080×1920, 30fps. 웹 전체 재생 확인. 실제 음성 청취는 사용자 웹 리뷰 대기이며 수치 검사로 청취 완료라고 주장하지 않는다.
- 변경: CUT03은 생성 원본의 개봉 후 구간 사용, CUT05는 둥근 모찌 형태 수정, CUT08은 사용자 승인에 따른 실제 패키지 외곽 마스크. 원본 v0001 보존.
- 상세 근거: `GumaVideoFactory/storage/handoffs/food-black-sesame-9719137731/production-v0005/README.md`, `resume-status.json`, `web-delivery-v2.json`. 완료 기록을 덮는 과거 checkpoint/prepare 스크립트는 다시 실행하지 않는다.

## 모바일 로딩 진단과 이어갈 일

- 사용자 관찰: 모바일에서 이미지 생성 도구를 많이 사용한 대화에 로딩 실패가 집중된다. 이미지가 많은 새/기존 대화를 같은 모바일 환경에서 비교할 근거이며 생성 도구 자체의 결함이 확인된 것은 아니다.
- 2026-10-08 측정에서 Main 원본 세션 JSONL은 약 139.85 MiB, 그 안의 인라인 이미지 문자열은 약 117.37 MiB였다. 중복 기록 포함 522회, 고유 데이터 492개. 생성 이미지뿐 아니라 스크린샷·검수 이미지가 포함된다. 이는 전송량이나 모바일 RAM 실측치가 아니다.
- Food 약 268.99 MiB, Living 약 151.52 MiB, 짧은 `모바일 원격 접속 상태 확인` 대화 약 0.99 MiB. Main에서 기존 compact 기록 8회가 확인되었지만 원본 이력은 여전히 크다.
- PC 여유 RAM은 약 12.3 GiB. 검사한 10월 7일 데스크톱 로그에는 메모리 부족 메시지는 없었고 원격 websocket 연결 실패·재연결 기록은 있었다. 모바일 실패 원인을 하나로 확정하지 않았다.
- 예방 지침은 루트 AGENTS.md에 반영했다. 기존 대화 기록·DB·첨부파일은 변경하지 않았다.
- 사용자 결정: 2026-10-08 새 Main-Mobile 생성 제안에 **현재 대화 유지**를 선택했다. 새 대화를 만들거나 역할 주소를 변경하지 않는다. 이 문서는 보존용 요약으로 둔다.
- 현 대화에서는 텍스트 중심 상태 확인과 중복 이미지·대형 출력 억제를 즉시 적용한다. 필요한 이미지 생성·시각 검수는 계속 수행한다. 기존 누적 이미지를 제거하거나 모바일 표시 캐시를 비우는 지원 도구는 확인되지 않았다.
- 사용자가 모바일에서 재접속해 결과를 확인하기 전에는 로딩 해결을 주장하지 않는다. 증상이 지속되면 같은 시간대 연결 오류와 모바일 클라이언트 문제를 추가 조사한다. 향후 사용자가 대화 전환을 명시적으로 요청할 때만 이 요약으로 새 대화를 만드는 대안을 사용한다.

공식 참고: https://developers.openai.com/blog/mastering-codex-remote-for-engineering — `/compact`는 맥락 정리, `/fork`는 기존 이력 상속으로 설명된다.
