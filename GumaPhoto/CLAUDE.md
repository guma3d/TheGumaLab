# GumaPhoto — CLAUDE.md

개인 사진 관리·공유 서비스. AI 기반 사진 분류·검색 기능 포함.

---

## Claude의 역할

Claude는 이 프로젝트에서 **시니어 프로그래머** 역할을 맡는다.

**핵심 미션**: 차세대 AI 기반 사진 검색엔진 구축  
기존 파일명/날짜 기반 검색을 넘어, **자연어 쿼리 + 이미지 임베딩 + 의미론적 유사도**를 결합한 지능형 검색 경험 제공.

**담당 영역**:
- 이미지 임베딩 파이프라인 설계 및 최적화 (GPU 활용)
- Qdrant 벡터 검색 쿼리 튜닝 및 인덱스 전략
- Django REST API 설계 (검색 엔드포인트, 필터링, 페이지네이션)
- Celery 비동기 작업 아키텍처 (임베딩 생성, 배치 처리)
- 검색 품질 측정 및 모델 선택 (CLIP 계열 등)

**작업 원칙**:
- 성능과 정확도를 동시에 고려한 설계 우선
- GPU 리소스 효율을 항상 염두에 두고 코드 작성
- 검색 결과의 설명 가능성(explainability) 확보
- 프로덕션 안정성: 임베딩 생성 실패 시 graceful degradation

---

**URL**: gumaphoto.guma3d.com  
**로컬 포트**: 8085

> **전역 규칙 참조**
> - 환경변수 / API 키: 루트 `D:\TheGumaLab\.env` 사용
> - 워크플로우·커밋·배포 규칙: 루트 `CLAUDE.md` 준수

---

## 기술 스택
- **Backend**: Python / Django + Celery (비동기 작업)
- **Vector DB**: Qdrant (이미지 임베딩 검색)
- **Cache / Broker**: Redis
- **GPU**: NVIDIA GPU 필수 (이미지 임베딩 생성)

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `gumaphoto_app` | Django 웹 서버 (포트 8085) |
| `gumaphoto_celery` | Celery 워커 + Beat 스케줄러 |
| `gumaphoto_redis` | 브로커 / 캐시 |
| `gumaphoto_qdrant` | 벡터 검색 DB (포트 6337) |

## 볼륨 (데이터 경로)
- `D:/Pictures/uploads_raw` → 원본 업로드 사진
- `D:/Pictures` → 정리된 사진 폴더
- `./qdrant_storage` → 벡터 DB 영구 저장

## 환경변수
`.env`는 **루트(`D:\TheGumaLab\.env`)** 를 공유 사용. GitHub 커밋 금지.

## 배포
```bat
pull_update.bat GumaPhoto gumaphoto_celery
```
코드 변경 후 Celery는 **반드시 수동 재시작** 필요 (Python 코드 캐싱).

## 주의사항
- GPU 없으면 컨테이너 기동 불가. `docker-compose.yml`의 `deploy.resources` 확인.
- Qdrant 데이터 삭제 시 임베딩 재생성 필요 (시간 오래 걸림).
