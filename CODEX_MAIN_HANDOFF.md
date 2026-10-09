# Main 이어받기 — 2026-10-09

이 파일은 큰 이미지 이력을 복제하지 않고 Main 업무를 이어받기 위한 요약이다. 원본 대화와 제작 파일은 보존한다. 시점이 지난 상태는 실제 파일·웹에서 다시 확인한다.

## 환경과 기준 문서

- HomeServer Guma3D, 작업 디렉터리 `D:\TheGumaLab`, 저장소 `guma3d/TheGumaLab`, 기본 main. SSH origin과 상위 AGENTS.md의 커밋·동기화 지침을 따른다.
- 현재 Main: `01a10a44-3943-7d62-8798-5295f8100402`. 아직 대체 세션을 만들지 않았다.
- 제작 정책: `GumaVideoFactory/AGENTS.md`, `RESEARCH.md`, `README.md`, `app/core/production_rules.json`. Food/Tech/Living 역할·주소는 README가 기준이다.
- 한국어로 답한다. 비밀값은 출력·커밋하지 않는다. 파일과 웹의 버전 기록을 우선 사용하고 이전 전체 대화·이미지를 다시 불러오지 않는다.

## 지속되는 사용자 승인 원칙

- 2026-10-10 최신 승인: 새 공개 예정 영상은 구독 피드·알림 ON(최초 비공개 단계부터 확인), 제목·설명·썸네일은 기존 YouTube 영상에서 수정한다. 공개 승인은 별개며 낮은 조회수 때문에 삭제·재업로드하지 않는다. 두 공개 영상 `0Wa-VX-mTco`/`IQkkmVqJn6w`는 유지, 공개 후 약 60시간인 10월 12일 09시 KST에 재점검한다. 기준 데이터는 `GumaVideoFactory/storage/handoffs/reupload-diagnosis-20261010/observations.json`. 기존 알림 OFF 기록은 과거 이력이며 새 업로드 기본값이 아니다.

- 원본·수정본·최종본 모두 프로젝트 storage에 로컬 보존하고 웹에서 버전별 검토한다.
- 최종본이 완성되어도 사용자가 정확한 버전을 업로드 요청한 때만 YouTube에 업로드한다. 공개 승인은 별개다. 고급 기능 승인이 업로드·공개 승인을 뜻하지 않는다.
- 모든 신규 영상은 Food 승인 Zephyr 음성. 검증한 5곡 중 1곡을 무작위 선택하고 재시도에서는 같은 곡을 유지한다. BGM -25 LUFS 고정 음량, 대사 연동 감쇠·페이드 없음. 상세 수치는 RESEARCH.md를 따른다.
- 신규 Food·Tech·Living 공통으로 컷별 빈 공간의 Maple Bold 이중 외곽선·키워드 강조·단발 팝 자막과 이미지 생성 도구의 별도 썸네일이 필수다. 해당 영상 버전의 썸네일 검수·해시 없이는 웹 검토 완료/신규 업로드를 승인하지 않는다.
- 피드백은 관련 최신 MD와 실행 규칙에 반영하고 오래된 규칙을 정리한다. 버전별 과거 원본·검수 이력은 보존한다.
- 설명에는 `#광고` + 실제 제품/용도/주제 관련 태그 최소 5개(총 6개 이상)가 필수다. 중복·무관 태그는 제외하고 BGM 출처 앞, 수수료 고지는 마지막 줄에 둔다. 현재 등록 5편의 설명을 이 기준으로 수정·저장 확인 완료했으며 제목·가시성·영상은 유지했다. 증빙은 `storage/handoffs/description-hashtags-20261009/completion.json`이다.

## 누룽지팝 최신 상태 — 사용자 수용·비공개 등록 (2026-10-09)

- Food의 직접 사용자 메시지 “이건 한번에 성공!! 유튜브에 비공개로 등록해” 확인 후 `12681a1f9b25c2e8`의 Video v1 / Thumbnail v1만 [YouTube 비공개](https://www.youtube.com/watch?v=in626m-2X8Y)로 등록했다. [웹 버전](https://videofactory.guma3d.com/ideas/12681a1f9b25c2e8?video=1#Video), 8컷·31.97초, 영상 해시 `ce634cbb69e17cfd10bb009d5612b9c78bee190c6af27f46e146ec7f4fbd9874`.
- 실제 Studio에서 비공개·커스텀 썸네일·HD·검사 문제 없음·설명과 설정 저장 확인. 공개·상품 모음 추가 승인 없음. 채널 등록 6편(공개 2·비공개 4). 현재 옵션 일시품절과 사진 재사용 조건은 공개 전 재확인. 사용자 콘텐츠 수용을 에이전트 실제 음성 청취로 기록하지 않는다. 원본 해상도 제한과 세부 검수는 README 및 `storage/handoffs/food-nurungjipop-8989223435/`의 `completion.json`, `upload-completion-v0001.json`, `main-state.json`을 따른다.

## 가습기 최신 상태 — 콘텐츠 품질 미수용·동작 소스 재확보 중 (2026-10-09)

- **사용자 최신 판단이 우선한다.** Video v2는 ‘기능 설명 영상이 거의 없고 대부분 이미지에 의존한 매우 낮은 퀄리티’라는 피드백을 받았다. 아래 기술/프레임 검수와 웹 저장은 완료 이력이며 콘텐츠 품질 수용을 뜻하지 않는다. 최신 게시 상태는 `revision_requested`, 사용자 콘텐츠 검수는 `rejected`다. Living이 샤오홍슈와 제조사 공식 영상을 재조사 중이며 실제 확보 완료 전이다. Main은 새 급수·다이얼·분무·물통 분리/세척 동작 소스 인계 후에만 새 버전을 제작한다. 같은 이미지 중심 재렌더 금지. `content-feedback-v2.json`과 `main-state.json`이 최신 상태다.

- Living의 사용자 제작 승인 후, 추가 지시한 ‘쌀쌀하고 건조해진 가을, 샤오미 가습기로 방 안을 촉촉하게’ 주제를 반영했다. 아이템 `277d58f6dd54822d`, Preview v2 / Video v2, 32.033초·7컷·1080×1920·30fps. [정확한 웹 버전](https://videofactory.guma3d.com/ideas/277d58f6dd54822d?video=2#Video).
- 기존 Video v1은 보존한다. v2는 CUT1 음성·자막만 바꾸고 CUT2~7 영상과 Zephyr 음성을 재사용했다. Living의 `thumbnail-v2.png`는 이 아이템의 Thumbnail v1로 Video v2에 연결했다(파일 초안 번호와 웹 썸네일 번호는 별개). 생성 썸네일은 영상에 삽입하지 않았다.
- BGM은 최초 무작위 선정한 Fluffing a Duck 유지, -25.0 LUFS 고정·ducking/페이드 없음. 대사 -16.89 LUFS, 최종 피크 -3.17 dBTP. 전체 디코딩·컷별/전환 프레임 검수 통과. 실제 음성 청취는 수행하지 않았으며 사용자 웹 리뷰 대기다.
- 샤오미 공식 급수·세척·제품 사진, 실제 720×1280 다이얼/분무 영상, 별도 생성 시작·마무리 이미지를 구분해 기록했다. Living 720 원본 예외 적용, 최대 확대 1.362배. 다이얼 1.767초 뒤 다른 공식 사진으로 연결하며 정지 프레임 연장·반복 재생은 하지 않는다.
- 설명에 `#광고 #샤오미 #가습기 #가전 #가을 #상부급수 #생활용품 #쇼츠` 및 간결 BGM 출처·마지막 줄 수수료 고지를 준비했다. 현재 상품 URL은 일반 쿠팡 URL이며 제휴 링크가 아니다. 파트너스 링크 발급·도착 검증, 제3자 영상 권리 및 모델 라벨 미확인은 게시 전 확인 항목이다. YouTube 업로드·공개 승인 및 실행은 없으며 상품 모음에도 추가하지 않았다.
- 승인·원본·프롬프트·제작 스크립트·수정 근거는 `GumaVideoFactory/storage/handoffs/living-dryness-20261009/`, 최신 상태는 `main-state.json`, 완료 증빙은 `completion-v2.json`을 확인한다. 최종 영상은 `storage/products/277d58f6dd54822d/Video/v0002/final.mp4`에 있다.

## 최근 확인한 결과 — 현재 상태와 이력을 구분

- 아래 공개·비공개 상태는 2026-10-09 Studio 확인 기록 기준이다. 현재 상태를 다시 물으면 실제 채널과 대조한다. 과거의 빈 채널·삭제 대기·흑임자 v2 검토 상태는 현재 상태가 아니다.
- 채널 `UCRtAVFQFmJCcpvLeuyq03Kg` / `@GumaShop86`: Standard·Intermediate·Advanced 기능 사용 가능. 고급 기능은 2026-10-08 Studio에서 Enabled 확인.
- 공개: 고구마빵(`372a4996226cf3a5`) Video v13 / Thumbnail v2 → https://www.youtube.com/watch?v=IQkkmVqJn6w, 미지아 보풀제거기 2(`57ab7c7af6717633`) Video v11 / Thumbnail v1 → https://www.youtube.com/watch?v=0Wa-VX-mTco. 사용자 별도 교체 요청에 따라 팝 자막·생성 썸네일을 적용하고 기존 AAC 오디오 스트림·장면·제목·설명을 보존했다. 이전 `T0eKHI5ieXA`·`uSQqUUQ1GCc`는 후속 사용자 요청으로 YouTube에서 삭제했고 로컬 버전은 보존한다.
- 비공개 최신본: 딸기쏙우유 찹쌀떡(`67e70b2aebfc411e`) Video v17 / Preview v10 / Thumbnail v1 → https://www.youtube.com/watch?v=yqG4SXzqpCA, 흑임자인절미(`dadc1759bf7912ef`) Video v6 / Preview v6 / Thumbnail v1 → https://www.youtube.com/watch?v=fKpQ14VtPMY, 피자설기 v3 → https://www.youtube.com/watch?v=yypR1nJVmic. 찰떡아이스·딸기떡은 Food의 직접 사용자 요청으로 팝 자막·별도 생성 커버를 적용해 비공개 교체했고, 새 업로드 검증 뒤 이전 `bBdkw1fdikM`·`5qAtgvCnDZE`를 삭제했다. 기존 최종 AAC와 사용자 제목·설명은 보존했다. 이 세 편의 공개 승인은 없다. 현재 채널은 공개 2개·비공개 3개, 총 5개다. 다음 버전은 별도 업로드 요청이 필요하다.
- 상품 모음: https://videofactory.guma3d.com/products. 따뜻한 노란색·크림 테마, 실제 제품 사진, 모바일 한 열 카드. 승인된 공개 상품 01 고구마빵·02 미지아만 노출한다. 비공개/웹 검토 제품은 자동 추가하지 않는다.
- 사용자가 직접 수정한 제목·설명이 게시 문구 기준이다. 제목 앞 [광고]를 붙이지 않고 설명은 글머리, BGM 출처는 간결한 하단 한 줄, 정확한 쿠팡 수수료 고지는 마지막 줄. 기존 음원은 출처 표시 조건을 준수한다.
- 찰떡아이스 첫 장면은 정확한 공식 제품 표지 원본 이미지로 교체했다. 노이즈가 있는 생성 포장 합성을 재사용하지 않는다. 기존 로컬 버전·승인·검수 이력은 보존한다.
- 최신 근거: `GumaVideoFactory/storage/handoffs/private-pop-thumbnails-20261009/completion.json` 및 같은 폴더 `studio-final.txt/png`, `web-verification.json`, 제품별 검수·커버 프롬프트. 이전 공개본 교체·삭제는 `common-pop-thumbnails-20261009/completion.json`, `youtube-cleanup.json`이며 과거 승인·검수 기록은 수정하지 않는다. 제품별 최종 버전/BGM 표는 README가 기준이다.

## 파트너스 확인 범위와 후속 작업

- 공개 두 상품의 링크 도착 상품·옵션과 공통 추적 ID `AF4083845`를 확인했다. 계정 소유자와 추적 ID의 일치, 계정 승인·등록 매체, 실제 클릭·주문·수익은 로그인 전이므로 미확인이다. 링크 이동 성공을 수익 발생/정산 보장으로 기록하지 않는다.
- 홈서버 브라우저 로그인 후 계정/등록 매체와 조회 기간별 리포트를 확인한다. 휴대폰의 별도 브라우저 로그인은 홈서버로 자동 공유되지 않는다. 모바일 Codex 로그인 화면 직접 조작 지원은 미검증이다. 비밀번호·인증번호·쿠키를 기록하거나 전달받지 않는다.
- 실적 자동 수집·대시보드 연동은 구현하지 않았다. 신규 자동 조회/공개를 완료된 것처럼 공유하지 않는다.

## 추가 제작 — 피자설기

- 아이템 `e9d3b5997cf329dd`, 웹 리뷰 https://videofactory.guma3d.com/ideas/e9d3b5997cf329dd#Video.
- 기존 완료본 Preview v1 / Video v2(28.33초, 8컷, Carefree, Zephyr)를 보존했다. 제3자 푸드킹덤 촬영의 재사용 허가는 미확인이다. 사용자는 후속 Video v3를 확인하고 정확한 버전의 비공개 업로드만 승인했으며 완료했다. 공개 승인은 없다.
- 최신 승인 board-v0002: 기존 8컷의 소스·대사·순서는 그대로 두고 첫 컷에 피자설기 화제성+수라당 로켓프레시 소개 추가, 컷별 빈 공간을 이용한 상하 자막 위치 조정. Preview v2 / Video v3(34.67초) 제작·화면/기술 검수 완료. 정확한 웹 링크는 https://videofactory.guma3d.com/ideas/e9d3b5997cf329dd?video=3#Video. 별도 AI 생성 Thumbnail v1을 웹 커버와 YouTube에 등록했고 영상에는 삽입하지 않았다. Studio 비공개·HD·실제 커버 저장을 확인했다.
- 상태·해시·검수·링크 기준: `GumaVideoFactory/storage/handoffs/food-pizza-seolgi-9719378135/main-state.json`, 최신 완료 `completion-v0002.json`. 과거 `completion.json`은 Video v2 이력이다. 원본 승인 해시와 최신 사용자 기존 컷 보존 지시를 대조한다.
- 자막의 폰트·색·크기 체계는 통일하고 위치는 컷별 주요 제품·동작·포장 인쇄를 피한다. 컷 안에서는 고정한다. 기존 영상·음성은 재생성하지 않으며 수정 버전 BGM은 Carefree를 유지한다. 새 첫 컷 음성만 생성한다.
- 실제 청취를 수행하지 않았으면 사용자 웹 음성 리뷰 대기로 남긴다. 기술 검사·브라우저 전체 재생은 실제 청취 검수와 구분한다.

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
