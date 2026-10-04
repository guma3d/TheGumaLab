# 쇼핑쇼츠 운영·감독 절차

09시 테크·15시 음식·21시 생활용품 각 1편. 20~40대 대상, 채널 https://www.youtube.com/@GumaShop86. GPT-6 Astra가 조사·콘티를 직접 작성한다. 실제 모델이 다르면 변경을 요청하며 허위 기록하지 않는다.

## 선정·쿠팡

실제 검색·제조사 원문·게시일 확인: 최근 7일 우선, 최대30일 근거와 공식 영상/이미지 필수. 없는 날짜·인기·가격·효능을 만들지 않는다. 핵심 및 추가 기능2개를 검증한다. 전체 제품 이력과 Studio 최근7일 동영상·Shorts(비공개 포함)의 유사 주제·해결 문제를 제외한다. 사용자 지정 재편집은 새 추천과 구분한다.

인앱 브라우저 우선, 필요시 Chrome. 동일 모델·옵션의 공식 판매처와 로켓배송을 각각 확인한다. 판매자로켓·직구로 대체하지 않는다. 실제 발급된 파트너스 URL의 연결을 검증한다. 로그인·본인인증은 요청하며 우회하지 않는다. 테크는 확인 가격50만원 이하만 제작한다.

Recommendation 필드와 URL 검증은 recommendations.py를 따른다. purchase_link에 url, seller, option, official_evidence, rocket_evidence, checked_at(24시간), affiliate_url, affiliate_evidence, price_krw, price_evidence를 저장한다. sources와 technical_video 또는 official_images 필요. topic_key, problem_key, novelty_review의 Studio 확인·영상별 비교 근거도 기록한다.

## 제작 전 감독

categories.py의 글꼴·색감·자막 위치·Achird 남성 음성(사용자 선택 2번)를 유지한다. 테크는 기술과 생활 문제, 음식은 최근 유행과 실제 질감, 생활용품은 불편과 쓰임을 연결한다. 한국 디저트 상황극은 한국의 젊은 성인 여성, 예열 마크는 짧은 설명만. 사용 경험·동일한 맛·인기 순위를 꾸미지 않는다.

Board(author_model=gpt-6-astra)는 필요성→솔루션→관심 이유→제품 소개→고정댓글·채널 프로필 고정 CTA 순서6~8컷. Cut 구조는 shopping.py 참조. 첫 컷 hook, 짧은 headline과 대사, 컷2~6초. 인기 주장에는 원문 근거. 공식 실물 보존, 맥락 컷만 Veo, 필요한 보조 이미지는 생성 가능. Gemini 기획·3D 모델은 사용하지 않는다.

원본 짧은 변: 영상1080px·이미지720px 이상, 확대1.5배 이하. 낮은 해상도를 확대해 고해상도로 가장하지 않는다. 가로 원본은 원본색 배경이나 검수한 크롭 사용. 검은 여백 금지. 소스·전 컷 프레임·제품 정확성·기능 대응·구도·템포를 실제 확인한다.

## 제작·검수·업로드

명령은 `docker exec GumaVideoFactory_app python shopping_package.py`로 실행한다.

1. `build 후보.json --file 콘티.json`: 새 Preview에 원본·컷·시트 저장. 모든 컷과 구간을 직접 본다.
2. `seal ID --version N --file 검수.json`: reviewed_by, passed, board_sha256, scenes[{number,passed,notes}], preflight(quality.PREFLIGHT_AXES 전부true), unresolved_issues=[] 필요. 검수 해시 고정.
3. `enqueue ID --version N`: 음성 길이를 먼저 검사하고 FIFO로1080p Veo·1080×1920·30fps 합성. --regenerate는 새 버전. 실패한 유료 요청을 맹목적으로 재시도하지 않는다.
4. `pending`: 완성본 전 컷 화면·자막·템포·발음·음량·말투 검수. 미달 컷은 수정한 새 버전. `review ID --version V --file 검수.json`에 audio_visual_passed, listened_to_audio=true, file_sha256, scores(quality.REVIEW_AXES 각8~10), notes, unresolved_issues=[] 기록. 청취 불가 시 사용자 선택 Achird·기술·화면 검수를 근거로 review_private를 사용하고 audio_review=user_review_on_private_youtube로 기록한다. 청취했다고 가장하지 않는다. 같은 원본 최대2회·연속 금지, 유사 장면·대사 행동 대응·밝은 저대비·0.2초 전환·오른쪽 위 [광고]·영상/설명 수수료 고지 검수, 왼쪽 위 브랜딩 제거.
5. `claim` 후 computer-use Studio에서 채널·기존 업로드 확인, upload.json과 final.mp4로 비공개 업로드. 실제 가시성·URL 확인 후 `private`에 notes, visibility=private, channel, url 기록. uploading이 남으면 Studio부터 확인해 중복을 막는다.
6. 비공개 완료된 새 아이템1개를 해당slot DailyBatch로 recommendation_import.py에 저장한다. 날짜 목록·시간별history 누적, 기존 결과와 버전 보존. 준비 미달이면 기존 목록 유지하고 부족 개수를 알린다. API의 상태·URL·날짜·history 검증.

## 수정·공개·정리

`edits`의 아이템·부모 버전·CUT 번호·대사·피드백을 반영해 새 버전 제작 후 비공개 업로드하고 `edit-done`으로 기록한다. 과거 소스 경로·출처를 보존한다. 제외 아이템은 보관 처리하며 삭제하지 않는다.

사용자의 해당 버전 공개 승인(publish_requested) 이후에만 같은 URL을 공개로 전환하고 `public` 기록. 자동 제작·비공개 업로드는 승인됨. 완료를 가장하지 않으며 새 완료·실패·필요한 조치만 간결히 알린다. 동일 상태는 조용히 유지한다. 작업용 탭은 닫고 사용자 탭은 보존한다.
