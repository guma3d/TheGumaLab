# GumaPhoto — CLAUDE.md

개인 사진 관리·공유 서비스. AI 기반 사진 분류·검색 기능 포함.

**URL**: gumaphoto.guma3d.com  
**로컬 포트**: 8085

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
