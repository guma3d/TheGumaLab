# GumaVideoFactory

Codex가 준비한 클립·콘티·3D 묶음을 검토하고 최종 승인으로 영상을 제작합니다.
공개 주소: https://videofactory.guma3d.com · 홈서버 포트: 8085.

## 제작 흐름

테크: 09·21시 Codex 사전 준비 → 완성 묶음 추천 → 최종 승인 → Veo 전환·영상 합성. 음식은 실사 자료 → 프리뷰 → 영상입니다.

- 신형 테크·트렌드 음식은 탭으로 구분합니다. 생성 버튼은 이동 없이 진행 막대·상태를 갱신합니다. 상단 오른쪽 ↻는 현재 주소·탭을 유지해 화면을 새로 불러오며 진행 중인 서버 제작은 계속됩니다.
- 제품 **제목**을 누르면 `/ideas/<id>` 상세 페이지에서 단계·버전·참고자료를 확인하고 모델을 승인합니다. 제목으로 처음 열 때는 아이디어 작업 공간만 등록하며 유료 생성을 시작하지 않습니다.
- 프리뷰·3D는 상태 표시만 제공합니다. 유료 사전 생성·재생성 버튼은 제거했습니다. 제목을 눌러 자료·버전을 확인하며 최종 제작만 버튼으로 실행합니다.
- 사전 준비는 공식 클립 6~8컷·대표 이미지·자체 대본·필요한 3D입니다. Codex가 구간별 기능과 네 방향 모델을 검수하고 파일 해시를 고정합니다. 자료 변경 시 최종 제작을 차단합니다. 최종 확인에서 클립·대본·3D·HTTPS 상품 링크를 함께 승인합니다.
- 제작 보관함은 12개씩 페이지로 나눕니다. 이전 작업은 `/legacy/<id>`에서 읽기 전용으로 확인합니다. 새 버전이 과거 영상·프리뷰의 부모 버전을 바꾸지 않습니다.

## 제품과 영상 품질

**실물 외형 일치가 우선입니다.** 외형은 승인된 Blender 모델·실제 제품 자료로 제작합니다. 생성형 이미지·Veo는 완제품 없는 원리 설명에만 사용하며 실제 내부 설계로 주장하지 않습니다.

테크는 공식 영상의 실제 시간표 프레임으로 기능별 구간을 선정·재검토합니다. 원본·구간·해시를 보존하고 자체 나레이션을 사용합니다. 재생성은 검증한 원본을 재사용합니다. 공식 재사용은 사용자 작업 가정입니다. 3D는 승인 모델로 보완하며, 형상 미확보 시 원리 표현으로 표시합니다.

음식은 최신 트렌드의 실제 사진·영상으로 식감·조리·먹는 장면을 설명하고 식품·재료로 연결합니다. 자료의 출처·제작자·사용 조건을 확인합니다. 공개 자료나 짧은 발췌라는 이유만으로 사용 권한을 추정하지 않습니다. 자료가 없으면 실사 자료 등록을 기다립니다.

## 모델 준비

Codex가 공개 제조사 모델·실제 사진을 조사합니다. 확보한 모델은 정적 메시와 검증 가능한 PBR 재질만 안전하게 변환합니다. 외부 스크립트·드라이버는 실행하지 않습니다. 정확한 형상을 확보하지 못하면 실제 제품과 구별되는 원리 표현으로 제한합니다.

Blender에서 네 방향 렌더를 확인하고 출처·한계·해시를 기록합니다. 제품별 치수를 다른 기종에 적용하거나 임의 부품을 만들지 않습니다. 검수와 사용자 최종 승인은 별개이며, 수정은 새 버전으로 남깁니다.

## 저장 구조와 공통 컨텍스트

```text
storage/products/<product-id>/
  idea.json
  inputs/
  3DModel/v0001/  # version.json, model.blend, view_*.png, 출처·검사 기록
  Preview/v0001/  # 공식 원본·출처, 콘티, scene_*.png/mp4, 검증 기록
  Video/v0001/    # version.json, 컷 영상·음성·완성 영상
```

새 버전에 공통 규칙 사본·revision·해시와 제품별 검증 근거를 보존합니다. `app/core/production_rules.json`을 갱신해 피드백을 다음 제작에 적용합니다.

피드백 반영 시 공통 코드·규칙·회귀 검증을 함께 갱신합니다. 관련 Markdown은 오래된 설명을 교체하고 중복을 합쳐 전체 분량을 늘리지 않습니다. 변경 이력은 Git에 남기며 README에 누적하지 않습니다.

## 추천 조사

한국시간 매일 **09:00·21:00**, 공식 기술 영상이 확인된 새 테크 제품 **3개씩** 추천합니다. 정식 제품명으로 전체 이력 중복을 차단하며 추천 기록은 제작 초기화와 별도로 보존합니다. 조사 지침·입력 스키마는 `RESEARCH.md`를 따릅니다. Codex 예약 조사는 PC와 앱이 실행 중이어야 합니다. 예약 조사는 로컬 FFmpeg·Blender로 사전 제작까지 완료합니다. 별도 생성 API는 사용하지 않습니다.

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
| PLANNER_MODEL | 레거시 설정, 테크 사전 준비에서는 호출 금지 |
| IMAGE_MODEL | 레거시 설정, 테크 사전 준비에서는 호출 금지 |
| VEO_MODEL | veo-3.1-fast-generate-preview, 개념 영상 |
| DEFAULT_VOICE | ko-KR-SunHiNeural |
| PORT / HOST | 8085 / 0.0.0.0 |
| BLENDER_VIDEO_WIDTH | 720 또는 1080 |

호스트 개발 실행은 Python 의존성, FFmpeg, Blender가 준비된 상태에서 `uvicorn app.main:app --host 0.0.0.0 --port 8085`를 사용합니다. 운영은 Docker Compose를 사용합니다.

테크 사전 준비는 Codex 이용 한도와 로컬 자원을 사용합니다. 최종 Veo 제작은 API 비용이 발생합니다. Blender 제품 컷은 로컬 렌더링하며 음성 길이에 맞춰 합성합니다. 사용 모델이나 결제 잔액은 외부 서비스 설정에 따라 달라지므로 문서에 잔액을 고정하지 않습니다.

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
