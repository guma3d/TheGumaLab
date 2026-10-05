# GumaVideoFactory

쇼핑쇼츠 조사·제작·YouTube 비공개 리뷰와 컷별 피드백 작업실.
https://videofactory.guma3d.com/ · 홈서버 8085 · https://www.youtube.com/@GumaShop86

## 문서 구조
- [AGENTS.md](AGENTS.md): 에이전트 운영·권한·보존 원칙.
- [RESEARCH.md](RESEARCH.md): 전체 공통 / 신형 테크 / 트렌드 푸드 / 생활용품 / 공통 2회 검수와 실행 절차. 제작 기준은 이 문서를 우선한다.
- app/core/production_rules.json: 실행에 전달하는 규칙. categories.py: 카테고리 스타일·음성 설정.

## 서비스 흐름

한국시간 09시 테크·15시 푸드·21시 생활 각 1편. 조사·쿠팡 검증 → 강한 후킹의 6~8컷 콘티 → 제작 전 검수 → 영상 제작 → 제작 후 검수 → 비공개 업로드 → 사용자 버전 승인 후 공개.

공통 메이플스토리 Bold·외곽선 자막·배경 박스 없음. 반복 AI·쿠팡 고지 자막은 제외하고 [광고]와 설명·업로드 설정의 고지는 유지한다. 음식 Zephyr 여성, 나머지 Achird 남성. 전체 컷의 스타일을 통일하고 동일·유사 화면을 반복하지 않는다.

아이템 제목을 열어 CUT 영상·대사·버전을 확인하고 피드백을 저장한다. storage/products/<id>/Preview/vNNNN과 Video/vNNNN에 원본·콘티·음성·최종본·검수 해시·게시 기록을 보존한다. 신규 3D 단계는 없으며 과거 파일만 보존한다.

## 실행·설정
```powershell
cd D:\TheGumaLab\GumaVideoFactory
docker compose up -d --build
```
.env.example을 참고한다. 키·쿠키·비밀번호는 출력·커밋 금지. Veo API 기본 모델은 veo-3.1-fast-generate-preview이며 유료다. 음식은 브라우저 Flow 크레딧으로 생성하며 API로 대체하지 않는다. 음성 설정은 categories.py, 제작·재사용은 shopping.py를 따른다. Python·FFmpeg 등 의존성은 Docker 이미지로 관리한다.

## 검증·배포
상위 AGENTS.md에 따라 검증 → 커밋 → pull/rebase → main push. 재시작이 필요하면 제작 큐가 비었는지 먼저 확인한다. `python -m unittest discover -s tests -p test_shopping.py -v`로 제작 경로를 검증하며 테스트에서 유료 호출은 모의 처리한다. 대용량 영상·데이터는 Git에 넣지 않는다. 문서는 낡은 규칙을 교체·통합해 전체 분량을 유지한다.
