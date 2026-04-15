# GumaPhoto — CLAUDE.md

가족 사진 관리 서비스. AI 기반 개인화 검색 + 사진 정리 + 메타데이터 피드백 시스템.

---

## Claude의 역할

Claude는 이 프로젝트에서 **시니어 프로그래머** 역할을 맡는다.

**핵심 미션**: 차세대 AI 기반 가족 사진 검색엔진 구축  
자연어 쿼리 + 이미지 임베딩(SigLIP) + 가족 프로필 기반 개인화 검색.

**담당 영역**:
- 이미지 임베딩 파이프라인 설계 및 최적화 (GPU 활용)
- Qdrant 벡터 검색 쿼리 튜닝 및 인덱스 전략
- FastAPI REST API 설계 (검색, 피드백, 시스템 엔드포인트)
- Celery 비동기 작업 아키텍처 (Organizer → Indexer → Cache Rebuild)
- Gemini NLP 쿼리 파싱 및 가족 개인화 검색 품질 최적화

**작업 원칙**:
- 성능과 정확도를 동시에 고려한 설계 우선
- GPU 리소스 효율을 항상 염두에 두고 코드 작성
- 프로덕션 안정성: 임베딩 생성 실패 시 graceful degradation

---

**URL**: gumaphoto.guma3d.com  
**로컬 포트**: 8085

> **전역 규칙 참조**
> - 환경변수 / API 키: 루트 `D:\TheGumaLab\.env` 사용
> - 워크플로우·커밋·배포 규칙: 루트 `CLAUDE.md` 준수

---

## 기술 스택
- **Backend**: Python / FastAPI + Celery (비동기 작업)
- **Vector DB**: Qdrant (`gumaphoto_hybrid_kr` 컬렉션)
- **AI Models**: SigLIP (이미지 임베딩), InsightFace (얼굴 인식), Gemini (NLP 쿼리 파싱)
- **Cache / Broker**: Redis
- **Frontend**: Vanilla JS (모듈 구조) — 프레임워크 없음
- **GPU**: NVIDIA GPU 필수 (이미지 임베딩 생성)

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `gumaphoto_app` | FastAPI 웹 서버 (포트 8085) |
| `gumaphoto_celery` | Celery 워커 + Beat 스케줄러 |
| `gumaphoto_redis` | 브로커 / 캐시 |
| `gumaphoto_qdrant` | 벡터 검색 DB (포트 6337) |

## 볼륨 (데이터 경로)
- `D:/Pictures/uploads_raw` → 원본 업로드 사진
- `D:/Pictures` → 정리된 사진 폴더 (`YYYY/YYYY-MM/` 구조)
- `./data` → 앱 데이터 (캐시, DB, 가족 프로필 등)
- `./qdrant_storage` → 벡터 DB 영구 저장

## 핵심 데이터 파일 (./data/)
- `family_profile.json` — 가족 구성원 프로필 (생년월일, 역할, 별명). 나이/생애단계 검색에 사용
- `known_faces.pkl` — InsightFace 얼굴 임베딩 학습 데이터
- `available_tags.json` — Qdrant에서 추출된 장소/날짜 태그 목록
- `caches/timeline_cache.json` — 홈 타임라인 캐시 (인덱싱 후 자동 재생성)
- `audit_trace.json` — 피드백 BEFORE/AFTER 기록 (JSONL)

## 업로드 → 검색 파이프라인
```
사진 업로드 → FileUploaded 이벤트
→ Organizer (YYYY/YYYY-MM 폴더 정리, 중복 제거, 썸네일 생성)
→ FileOrganized 이벤트
→ Indexer (SigLIP 임베딩 + InsightFace 인물 + GPS 장소 + Qdrant 저장)
→ Timeline Cache 자동 재생성
```

## 작업 라우팅 — 어느 컨테이너에서 실행되나
**gumaphoto_celery** (task 등록: `tasks.dispatch_event`, `tasks.indexer`, `tasks.organizer`)
- FileUploaded/FileOrganized 이벤트 디스패처, 벡터 인덱서, 파일 정리기
- 재시작 대상: `Scripts/vector_indexer.py`, `api/tasks.py`, `Scripts/organizer*.py`, 그리고 인덱서가 직접 쓰는 공용 모듈(`api/services/insightface_service.py` 등)

**gumaphoto_app** (FastAPI + `BackgroundTasks`)
- 모든 REST 라우터, **피드백 처리(`process_time_location_feedback`, `process_face_enrollment`)**, 타임라인 캐시 재생성, 검색 쿼리
- 재시작 대상: `api/routers/*.py`, `api/services/feedback_service.py`, `api/services/feedback_cache.py`, `api/utils/metadata_parser.py`, `api/utils/metadata_editor.py`, `core/state.py`, `main.py`

> ⚠️ **흔한 함정**: "피드백이 안 먹어요" 류 버그를 잡을 때 `gumaphoto_celery`만 재시작하면 의미 없음. 피드백은 Celery가 아니라 app 프로세스의 `BackgroundTasks`로 돌아간다. 공용 모듈(`api/services/feedback_service.py`, `api/utils/metadata_parser.py` 등)을 수정했다면 **양쪽 다** 재시작하는 것이 안전.

## 피드백 파이프라인 (`/api/feedback_v2/submit`)
1. **라우터 (app 프로세스, 동기)**: 이슈 타입별 Gemini 교정 → **Qdrant payload 즉시 업데이트** (UI 실시간 반영용)
2. **BackgroundTasks (app 프로세스, 비동기)**
   - `process_time_location_feedback`: 물리 EXIF 덮어쓰기 (`MetadataEditor.stamp_metadata`) + Qdrant 재병합 + audit trace 기록 + Auto Rollback
   - `rebuild_timeline_cache`: 홈 타임라인 캐시 재생성 (라이트박스 잔상 방지)
   - 인물 피드백은 `process_face_enrollment`가 `known_faces.pkl` 갱신
3. **FeedbackCache**: 처리된 ID를 디스크 큐에서 제거 (`remove_processed`)

**날짜 피드백 시 주의**: UI는 `YYYY-MM` 형식만 전송하지만, `stamp_metadata`는 EXIF에 `YYYY-MM-15 12:00:00`을 기본값으로 찍음. 라우터/서비스 양쪽 모두 이와 동일한 합성 날짜로 `parse_time_and_season`을 호출해 `season` + `time_of_day(=낮)`을 Qdrant에도 맞춰 넣는다. EXIF와 Qdrant의 불일치 방지.

## audit_trace.json (피드백 감사 로그)
- **형식**: JSONL. 한 줄 = `{"type": "BEFORE"|"AFTER", "trace_id": <point_id>, ...}`
- **페어링 규칙**: `trace_id`는 point_id이므로 같은 사진의 여러 피드백이 있을 수 있음. `GET /api/system/audit_logs`는 **순차 페어링**(`pending_before` 딕셔너리) 방식으로 모든 BEFORE/AFTER 쌍을 보존한다 — dict overwrite로 최신 1건만 남기면 안 됨.
- **프론트 렌더러**: `people`/`location`/`date` 텍스트 변경 + `geo_point` 좌표 변경을 모두 감지. 텍스트가 동일해도 좌표만 바뀐 피드백이 화면에서 사라지지 않도록 함.

## 검색 아키텍처
1. **로컬 파싱**: 인물명, 연도, 나이(`35살`), 연대(`30대`), 생애단계(`초등학교`) 추출
2. **Gemini NLP**: 나머지 텍스트에서 장소/계절/시간대/시각적 키워드 추출 (가족 프로필 컨텍스트 주입)
3. **Qdrant 필터**: 인물·장소·연도·계절·시간대 → `must` 하드 필터
4. **SigLIP 벡터 검색**: 시각적 키워드 → 영어 텍스트 임베딩 → 유사도 검색

## UI 구조
- **헤더**: 로고 + [업로드] [피드백] [시스템] 버튼
- **검색바**: 구글 스타일 상시 노출 검색창
- **홈**: 최신 사진 세로 무한스크롤 (인스타그램 스타일 그리드)
- **피드백**: 미분류 사진 인물/장소/날짜 교정 (EXIF 수정 + InsightFace 재학습)
- **시스템**: Qdrant 기반 통계 + 피드백 기록 조회

## 환경변수
`.env`는 **루트(`D:\TheGumaLab\.env`)** 를 공유 사용. GitHub 커밋 금지.

## 배포
```bat
REM 인덱서/organizer/이벤트 디스패처 변경
pull_update.bat GumaPhoto gumaphoto_celery

REM 라우터/피드백 처리/검색 변경 (대부분의 작업)
ssh HomeServer "docker restart gumaphoto_app"

REM 공용 모듈(utils/services) 변경 → 양쪽 모두
ssh HomeServer "docker restart gumaphoto_app gumaphoto_celery"
```
Python `sys.modules` 캐시 때문에 파일 bind mount만으로는 핫스왑이 안 된다. 함수 내부 `from ... import`도 최초 로드된 모듈을 재사용하므로 반드시 **프로세스 재시작**이 필요하다.

## 주의사항
- GPU 없으면 컨테이너 기동 불가. `docker-compose.yml`의 `deploy.resources` 확인.
- Qdrant 데이터 삭제 시 임베딩 재생성 필요 (시간 오래 걸림).
- `data/` 디렉토리는 `.gitignore` 대상 — `family_profile.json` 등은 볼륨에만 존재.
- 파일 이동 시 Qdrant의 `filepath` 필드도 반드시 함께 업데이트 필요.
- 타임라인 캐시는 인덱서 완료 시 자동 갱신. 수동 갱신: `POST /api/rebuild_cache`
