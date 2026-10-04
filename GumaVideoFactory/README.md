# GumaVideoFactory

쇼핑쇼츠 조사·컷씬·음성·영상 제작과 YouTube 비공개 리뷰를 관리합니다.
https://videofactory.guma3d.com/ · 홈서버 8085 · 채널 https://www.youtube.com/@GumaShop86

## 제작 흐름

09시 신형 테크·15시 트렌드 음식·21시 생활용품을 GPT-6 Astra가 각 1개 조사합니다. 공식 영상 또는 이미지와 쿠팡 공식 판매처·로켓배송·파트너스 링크를 먼저 검증합니다. 실행 모델은 Codex에서 Astra를 선택합니다.

필요성 → 솔루션 → 근거 있는 인기/관심 이유 → 제품 소개 → 채널 프로필 링크 CTA의 6~8컷을 작성합니다. Gemini 기획은 사용하지 않습니다. 공식 기술·제품·실제 음식 자료를 보존하고 적합한 후킹 컷만 Veo로 재제작합니다. 3D 모델 기능은 제거했으며 과거 파일은 보존합니다.

모든 영상에 ko-KR-SunHiNeural을 사용합니다. FIFO 제작·검수 후 computer-use로 비공개 업로드합니다. 웹에서 버전별 공개 승인 후 다음 Codex 실행에서 전환합니다. 로그인·인증은 사용자에게 요청합니다.

웹은 카테고리별 컷 편집 작업실입니다. 아이템 제목을 눌러 CUT 영상·대사를 확인하고 피드백을 저장합니다. 다음 Codex 실행에서 새 버전으로 반영합니다.

## 카테고리 기준

| 카테고리 | 구성과 고정 연출 |
|---|---|
| 신형 테크 | 생활 문제 → 기술 원리·핵심 및 추가 기능. 어두운 배경·민트 강조·정확한 공식 디테일. |
| 트렌드 음식 | 최신 유행 → 쿠팡 완제품 또는 재료·조리법. 따뜻한 색·실제 질감·조리 장면. 동일한 맛은 보장하지 않음. |
| 생활용품 | 생활 불편·계절 수요 → 사용 시연·장단점. 밝은 실사용 장면·파랑 강조. 커터·그릴·주방타월 등은 탐색 예시이며 현재 인기는 별도 검증. |

공통 글꼴 Noto Sans CJK KR·고정 음성·자막 위치를 사용합니다. 최근 7일 Studio 업로드와 로컬 업로드 이력을 비교해 비슷한 주제·불편을 반복하지 않습니다.

## 운영

RESEARCH.md의 검수·비공개 업로드 절차를 따릅니다. storage/products/<id>의 Preview/vNNNN에는 원본·콘티·검수 해시, Video/vNNNN에는 컷·음성·final.mp4·upload.json을 보존합니다. 실제 UI 확인 없이 업로드 성공을 기록하지 않습니다. 날짜별 추천·history도 보존합니다.

## 실행·설정

```powershell
cd D:\TheGumaLab\GumaVideoFactory
docker compose up -d --build
```

최초 설정만 .env.example을 .env로 복사하고 GEMINI_API_KEY(Veo용)를 입력합니다. 키·쿠키·비밀번호를 출력하거나 커밋하지 않습니다. VEO_MODEL 기본은 veo-3.1-fast-generate-preview입니다. PLANNER_MODEL·IMAGE_MODEL은 레거시용이며 신규 경로에서 사용하지 않습니다. 고정 음성은 shopping.py에 지정됩니다.

Python·FFmpeg·edge-tts가 필요하고 운영은 Docker Compose를 사용합니다. Veo에는 API 비용이 발생합니다. 실제 원본 재사용은 사용자 작업 가정으로 출처를 보존하며 권한 확보로 가장하지 않습니다.

## 검증·배포

루트 AGENTS.md에 따라 검증 → 커밋 → pull/rebase → main push. 필요시 제작 큐가 비었는지 확인 후 docker restart GumaVideoFactory_app. 새 흐름 검증은 `python -m unittest discover -s tests -p test_shopping.py -v`입니다. 유료 API는 테스트에서 모의 처리합니다.

코어 규칙은 app/core/production_rules.json에서 관리합니다. 관련 MD의 오래된 내용을 교체하고 중복을 합쳐 분량을 유지합니다. 이미지·대용량 영상과 데이터는 Git에 넣지 않습니다.
