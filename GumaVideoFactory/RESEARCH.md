# 하루 3회 쇼핑쇼츠 자동 제작

매일 한국시간 09·15·21시 각각 새 아이템 1개·영상 1개(하루 3개). 채널 https://www.youtube.com/@GumaShop86. PC·앱·연결된 브라우저가 필요하다. 실행 모델 GPT-6 Astra를 확인하고 다른 모델이면 사용자에게 변경 요청한다. 모델 이름만 기록해 대체하지 않는다.

## 조사와 쿠팡

실제 검색·원문·게시일 확인: 최근 7일 우선, 최대 30일 근거. 공식 영상 또는 이미지 필수. 전체 날짜·history와 정식 제품명 중복 검사. 가격·성능·인기는 추정하지 않는다. 핵심 기능과 추가 기능 2개를 검증한다.

인앱 브라우저 우선, 필요시 Chrome에서 쿠팡 파트너스를 사용한다. 동일 모델·옵션의 공식 판매처 근거와 로켓배송을 독립 검증한다. 판매자로켓·로켓직구로 대체하지 않는다. 실제 계정에서 발급한 파트너스 링크와 확인 근거를 저장한다. 로그인·인증 필요시 해당 작업을 보류하고 요청한다. 연결 오류와 구분하며 반복 알림은 피한다.

Recommendation 입력은 app/core/recommendations.py를 따른다. purchase_link: url(쿠팡 상세), seller, option, official_evidence, rocket_evidence, checked_at(최근 24시간), affiliate_url, affiliate_evidence. technical_video 또는 official_images[{title,url,published_date}] 필요. sources에는 최신 원문을 기록한다. 입력 JSON은 storage/recommendations/inbox에 저장한다.

## 컷씬과 제작

Astra가 공식 자료를 실제로 읽고 이미지·영상 프레임을 본 뒤 app/core/shopping.py의 Board JSON을 직접 작성한다. author_model=gpt-6-astra, title, summary, popularity_basis, popularity_claimed, popularity_source_url, cta_destination=channel_profile, scenes=6~8개.

각 컷: role(need/solution/reason/product/cta), mode(official_clip/official_image/veo), source_file(확보한 로컬 MP4/이미지), source_url, evidence, narration_ko, hook, covered_features, start_seconds, duration_seconds(2~10), veo_prompt, preserve_actual. role은 위 순서를 따르고 첫 컷 hook 필수. 인기 주장에는 원문 근거 필수, 없으면 관심을 끄는 이유로 설명한다. CTA는 채널 프로필 링크이며 하단·댓글 URL을 클릭하라고 하지 않는다. Veo 참고 이미지가 완성 장면인 것처럼 표시하지 않는다.

아래 명령은 docker exec GumaVideoFactory_app python shopping_package.py로 실행한다.

1. `build <후보.json> --file <콘티.json>`: 쿠팡 검증 후 새 Preview에 원본·컷·프레임 시트 저장. 출력 idea_id/number 기록. 모든 check_*_sheet를 실제 확인한다.
2. `seal <id> --version N --file <review.json>`: reviewed_by=gpt-6-astra, passed=true, board_sha256, scenes=[{number,passed,notes}]. 실물·기능·후킹·인기 근거·경계 검수 후 해시 고정.
3. `enqueue <id> --version N`: FIFO로 고정 음성·선택적 Veo·합성. 재생성은 --regenerate. 3D 모델은 생성·사용하지 않는다. 사전 승인 질문은 필요 없다. 실패한 유료 작업은 원인 확인 후 새 버전으로 처리한다.
4. `pending`: 완성 영상 위치와 업로드 상태 확인. 실제 영상과 음성을 재생·검수하고 `review <id> --version V --file <검수.json>`을 실행한다. JSON은 audio_visual_passed=true, notes(실제 검수 내용). 검수 불합격은 업로드하지 않는다.
5. `claim <id> --version V --file <근거.json>`으로 업로드 진행 기록 후 computer-use YouTube Studio에서 @GumaShop86과 기존 업로드를 확인한다. upload.json의 제목·설명·final.mp4를 사용하고 반드시 비공개로 저장한다. 로그인·파일 업로드 기능 차단은 요청한다. uploading 상태가 남으면 Studio 결과부터 확인하고 중복 업로드하지 않는다.
6. 실제 비공개 표시를 확인하고 `private <id> --version V --file <결과.json>` 실행. 결과는 notes, visibility=private, channel=https://www.youtube.com/@GumaShop86, url=https://www.youtube.com/watch?v=실제ID. 임의 성공 기록 금지.
7. 비공개 업로드된 새 제품 1개를 DailyBatch(date, researched_at, slot=09:00/15:00/21:00, items=[1개])로 recommendation_import.py에 저장한다. 하루 3회·회당 1개, 날짜 목록은 누적한다. 부족하면 기존 목록 유지·부족한 수 알림. 날짜·history·버전 삭제 금지. API의 준비 상태·비공개 URL·조사 시간·history를 검증한다.

## 컷 편집·공개 승인

`shopping_package.py edits`로 컷 수정 요청을 확인한다. 아이템·부모 영상 버전·cut_number·narration·feedback을 반영해 새 콘티 버전을 제작한다. 이전 source_file은 부모 Preview 폴더의 절대 경로로 해석하고 출처를 보존한다. 새 영상 비공개 업로드 후 `edit-done <id> --version 새영상번호 --file 요청ID`로 완료 기록한다. 사용자 리뷰는 YouTube 최종 영상으로 진행하며 GumaVideoFactory는 컷 영상·대사·수정 작업실이다.

## 공개 승인과 알림

웹에서 사용자가 영상을 리뷰하고 공개 승인하면 upload.json이 publish_requested가 된다. 다음 브라우저 작업에서 동일 URL·버전만 공개로 전환하고 `public` 명령에 notes, visibility=public, url을 기록한다. 승인 없는 공개·예약 공개는 금지한다. 실패·확인 불가를 성공으로 표시하지 않는다.

성공한 영상 1개의 제목·YouTube 비공개 URL과 https://videofactory.guma3d.com/ 를 안내한다. 새로운 실패·인증·연결 조치만 알리고 동일 상태는 조용히 유지한다. 자동화는 Codex 실행 시 브라우저를 조작하며 서버가 독립적으로 computer-use를 호출하는 구조는 아니다.
