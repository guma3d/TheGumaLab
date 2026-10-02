# GumaVideoFactory

추천 제품을 검토하고 3D 모델·실사 자료, 콘티, 영상을 단계별 승인으로 제작하는 서비스입니다.
공개 주소: https://videofactory.guma3d.com · 홈서버 포트: 8085.

## 제작 흐름

테크: 추천 → 공식 프리뷰·클립 → 필요한 경우 3D 생성·외형 승인 → 최종 승인·영상. 음식은 실사 자료 → 프리뷰 → 영상입니다.

- 신형 테크·트렌드 음식은 탭으로 구분합니다. 생성 버튼은 이동 없이 진행 막대·상태를 갱신합니다. 상단 오른쪽 ↻는 현재 주소·탭을 유지해 화면을 새로 불러오며 진행 중인 서버 제작은 계속됩니다.
- 제품 **제목**을 누르면 `/ideas/<id>` 상세 페이지에서 단계·버전·참고자료를 확인하고 모델을 승인합니다. 제목으로 처음 열 때는 아이디어 작업 공간만 등록하며 유료 생성을 시작하지 않습니다.
- 승인 완료와 다음 단계를 카드에 표시합니다. 완료된 생성 버튼은 비활성화하고 결과 확인은 제목으로 안내합니다. 오른쪽 **↻**는 새 버전을 생성합니다. 제작 중 중복 요청은 차단합니다.
- 테크 프리뷰는 6~8컷 공식 클립·대표 이미지·자체 대본입니다. 3D가 필요하면 “3D모델 생성 필요”를 표시하고 해당 프리뷰의 모델 승인까지 영상 버튼을 잠급니다. 목록의 Create Video는 같은 화면의 최종 확인 창에서 컷·대본·HTTPS 상품 링크를 검토한 뒤 제작합니다. 상세 페이지에서도 승인합니다. 수정하면 승인을 해제합니다.
- 제작 보관함은 12개씩 페이지로 나눕니다. 이전 작업은 `/legacy/<id>`에서 읽기 전용으로 확인합니다. 새 버전이 과거 영상·프리뷰의 부모 버전을 바꾸지 않습니다.

## 제품과 영상 품질

**실물 외형 일치가 우선입니다.** 외형은 승인된 Blender 모델·실제 제품 자료로 제작합니다. 생성형 이미지·Veo는 완제품 없는 원리 설명에만 사용하며 실제 내부 설계로 주장하지 않습니다.

테크는 공식 영상의 실제 시간표 프레임으로 기능별 구간을 선정·재검토합니다. 원본·구간·해시를 보존하고 자체 나레이션을 사용합니다. 재생성은 검증한 원본을 재사용합니다. 공식 재사용은 사용자 작업 가정입니다. 3D는 승인 모델로 보완하며, 형상 미확보 시 원리 표현으로 표시합니다.

음식은 최신 트렌드의 실제 사진·영상으로 식감·조리·먹는 장면을 설명하고 식품·재료로 연결합니다. 자료의 출처·제작자·사용 조건을 확인합니다. 공개 자료나 짧은 발췌라는 이유만으로 사용 권한을 추정하지 않습니다. 자료가 없으면 실사 자료 등록을 기다립니다.

## 모델 탐색과 변환

1. 공개 제조사 모델과 공식 사진을 검색하고 `.blend`, `.glb`, `.usdz`, `.obj`, `.fbx` 파일을 확보합니다. 로그인·결제를 우회하지 않습니다.
2. 공개 모델이 없으면 실제 사진을 분석해 제한된 JSON 기하 구조로 편집 가능한 초안을 만듭니다. 신뢰하는 빌더만 실행하며 AI가 작성한 Python을 실행하지 않습니다. 정확한 제품을 확인하지 못하면 오류로 표시합니다.
3. 외부 모델의 정적 메시를 가져오고 허용된 PBR 노드만 새로 구성합니다. 텍스처별 UV, 색상·거칠기·노멀·투명도 등을 보존하며 스크립트·드라이버·임의 노드 그룹을 복사하지 않습니다. 지원하지 않는 재질은 조용히 단순화하지 않고 실패로 표시합니다.
4. 네 방향 렌더와 실제 사진을 비교해 외형과 사용 조건을 승인합니다. 초안의 불확실성을 표시하며 사진 기반 복원이 정확한 설계임을 보장하지 않습니다.

여러 완제품이 포함된 자료는 검증된 기종·치수로 전체 부품 그룹 한 대를 선택합니다. 제품별 치수를 다른 기종에 적용하지 않습니다. `inspection.json`에 선택 근거와 Blender 버전을 기록합니다.

`1대만 분리 · 새 버전`과 `재질 복원 · 새 버전`은 다운로드 원본을 재사용하므로 다시 검색하지 않습니다. 수정 버전은 부모 번호·수정 사유·원본 해시를 기록하고 승인을 초기화합니다. 외부 편집기로 같은 파일을 덮어쓰는 방식은 자동 버전 관리에 포함되지 않습니다. 승인 파일 해시가 달라지면 후속 제작을 차단합니다.

## 저장 구조와 공통 컨텍스트

```text
storage/products/<product-id>/
  idea.json
  inputs/
  3DModel/v0001/  # version.json, model.blend, view_*.png, 출처·검사 기록
  Preview/v0001/  # 공식 원본·출처, 콘티, scene_*.png/mp4, 검증 기록
  Video/v0001/    # version.json, 컷 영상·음성·완성 영상
```

새 제작 버전은 `production_rules.json` 사본과 규칙 revision·해시를 기록합니다. 공통 피드백은 `app/core/production_rules.json`에서 관리하고 검색·모델 재구성·콘티에 전달합니다. 제품별 검증 근거는 별도로 유지합니다. 재생성은 새 폴더를 사용하며 실패 결과도 보존합니다.

피드백 반영 시 공통 코드·규칙·회귀 검증을 함께 갱신합니다. 관련 Markdown은 오래된 설명을 교체하고 중복을 합쳐 전체 분량을 늘리지 않습니다. 변경 이력은 Git에 남기며 README에 누적하지 않습니다.

## 추천 조사

한국시간 매일 **09:00·21:00**, 공식 기술 영상이 확인된 새 테크 제품 **3개씩** 추천합니다. 정식 제품명으로 전체 이력 중복을 차단하며 추천 기록은 제작 초기화와 별도로 보존합니다. 조사 지침·입력 스키마는 `RESEARCH.md`를 따릅니다. Codex 예약 조사는 PC와 앱이 실행 중이어야 합니다. 예약 조사는 생성 작업을 시작하지 않습니다.

## 실행과 설정

Docker 이미지에는 Python, FFmpeg, Blender가 포함됩니다. 홈서버에 Blender를 별도로 설치할 필요는 없습니다.

```powershell
cd D:\TheGumaLab\GumaVideoFactory
Copy-Item .env.example .env  # 최초 설정 시에만 실행
# .env에 GEMINI_API_KEY 입력
docker compose up -d --build
```

`.env`와 API 키는 출력하거나 커밋하지 않습니다. 주요 설정은 `app/config.py`와 `.env.example`을 참조합니다.

| 설정 | 기본값 / 용도 |
| --- | --- |
| GEMINI_API_KEY | Google API 키, 필수 |
| PLANNER_MODEL | gemini-3.8-flash, 검색·기획 |
| IMAGE_MODEL | gemini-2.5-flash-image, 테크 개념도 |
| VEO_MODEL | veo-3.1-fast-generate-preview, 개념 영상 |
| DEFAULT_VOICE | ko-KR-SunHiNeural |
| PORT / HOST | 8085 / 0.0.0.0 |
| BLENDER_VIDEO_WIDTH | 720 또는 1080 |

호스트 개발 실행은 Python 의존성, FFmpeg, Blender가 준비된 상태에서 `uvicorn app.main:app --host 0.0.0.0 --port 8085`를 사용합니다. 운영은 Docker Compose를 사용합니다.

검색·기획·생성 API는 비용이 발생할 수 있습니다. Blender 제품 컷은 로컬 렌더링하며 음성 길이에 맞춰 합성합니다. 사용 모델이나 결제 잔액은 외부 서비스 설정에 따라 달라지므로 문서에 잔액을 고정하지 않습니다.

## 배포와 검증

루트 AGENTS.md의 HomeServer 규칙에 따라 커밋 → pull/rebase → main 푸시로 배포합니다. 소스 마운트 방식입니다. 코드 반영 시 제작 완료 후 재시작합니다.

```powershell
docker restart GumaVideoFactory_app
docker exec GumaVideoFactory_app python -m unittest discover -s tests -q
docker exec GumaVideoFactory_app blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python /app/tests/blender_material_regression.py
Invoke-RestMethod http://localhost:8085/api/health
```

의존성·Dockerfile 변경 시 `docker compose up -d --build`로 재빌드합니다. 공개 접근은 Nginx·Cloudflare Tunnel과 중앙 인증을 사용합니다. 라우팅은 `Nginx/nginx.conf`, 상태는 `docker ps`로 확인합니다.

제작은 저장형 FIFO 큐에서 한 번에 하나씩 처리합니다. 화면에 대기 순번을 표시하고 재시작 후 미시작 작업은 이어갑니다. 중단된 실행은 실패로 남겨 자동 중복 과금을 피하며, 재생성은 새 버전입니다.
