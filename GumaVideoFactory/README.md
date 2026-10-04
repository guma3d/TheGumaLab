# GumaVideoFactory

쇼핑쇼츠 조사·컷씬·음성·영상 제작과 YouTube 비공개 리뷰를 관리합니다.
https://videofactory.guma3d.com/ · 홈서버 8085 · 채널 https://www.youtube.com/@GumaShop86

## 제작 흐름

매일 09시, 테크·음식 합계 3개를 GPT-6 Astra가 조사합니다. 공식 영상 또는 이미지와 쿠팡 공식 판매처·로켓배송·파트너스 링크를 먼저 검증합니다. Astra 실행 모델 설정은 Codex 채팅에서 선택하며 앱 서버가 모델을 임의 전환하지 않습니다.

필요성 → 솔루션 → 근거 있는 인기/관심 이유 → 제품 소개 → 채널 프로필 링크 CTA의 6~8컷을 작성합니다. Gemini 기획은 사용하지 않습니다. 공식 기술·제품·실제 음식 자료를 보존하고 적합한 후킹 컷만 Veo로 재제작합니다. 3D 모델 기능은 제거했으며 과거 파일은 보존합니다.

모든 영상에 ko-KR-SunHiNeural을 사용합니다. FIFO 제작 후 실제 화면·음성을 검수하고 Codex computer-use로 YouTube에 비공개 업로드합니다. 사용자가 웹에서 해당 버전을 공개 승인해야 공개 전환 대기에 들어갑니다. 실제 전환은 다음 Codex 브라우저 실행에서 수행합니다. 인앱 브라우저 우선, 필요시 Chrome; 로그인·인증 차단은 사용자에게 요청합니다.

웹은 카테고리 탭과 페이지별 보관함을 제공합니다. 제목으로 상세 컷씬·완성 영상·버전을 열고 공개를 승인합니다. 기존 방식의 프리뷰는 보관본으로 표시되며 신규 경로로 다시 준비해야 합니다. 과거 결과는 덮어쓰지 않습니다.

## 운영

`RESEARCH.md`의 shopping_package.py build → seal → enqueue → review → claim → private → recommendation_import.py 순서를 따릅니다. 실제 UI 결과 없이 업로드 성공을 기록하지 않습니다. upload.json에 파일 해시·영상 URL·이력을 남겨 중복 업로드와 미승인 공개를 차단합니다. 공개 승인 후 public 명령으로 관측 결과를 기록합니다.

storage/products/<id>/Preview/vNNNN에는 공식 원본·콘티·검수·해시가, Video/vNNNN에는 컷·음성·final.mp4·upload.json이 저장됩니다. 이전 3DModel 폴더는 보관용입니다. 날짜별 추천과 history를 삭제하지 않습니다.

## 실행·설정

```powershell
cd D:\TheGumaLab\GumaVideoFactory
docker compose up -d --build
```

최초 설정만 .env.example을 .env로 복사하고 GEMINI_API_KEY(Veo용)를 입력합니다. 키·쿠키·비밀번호를 출력하거나 커밋하지 않습니다. VEO_MODEL 기본은 veo-3.1-fast-generate-preview입니다. PLANNER_MODEL·IMAGE_MODEL은 레거시용이며 신규 경로에서 사용하지 않습니다. 고정 음성은 shopping.py에 지정됩니다.

Python·FFmpeg·edge-tts가 필요하고 운영은 Docker Compose를 사용합니다. 현재 이미지의 Blender는 과거 호환 의존성일 뿐 신규 제작에서 실행하지 않습니다. Veo에는 API 비용이 발생합니다. 실제 원본 재사용은 사용자 작업 가정으로 출처를 보존하며 권한 확보로 가장하지 않습니다.

## 검증·배포

루트 AGENTS.md에 따라 검증 → 커밋 → pull/rebase → main push. 필요시 제작 큐가 비었는지 확인 후 docker restart GumaVideoFactory_app. 새 흐름 검증은 `python -m unittest discover -s tests -p test_shopping.py -v`입니다. 유료 API는 테스트에서 모의 처리합니다.

코어 규칙은 app/core/production_rules.json에서 관리합니다. 관련 MD의 오래된 내용을 교체하고 중복을 합쳐 분량을 유지합니다. 이미지·대용량 영상과 데이터는 Git에 넣지 않습니다.
