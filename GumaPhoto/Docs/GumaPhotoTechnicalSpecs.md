# 🔍 GumaPhoto 모듈별 핵심 기술 명세서 (Technical Specifications)

이 문서는 GumaPhoto 시스템을 지탱하는 **핵심 프로세스(업로드, 폴더정리, 벡터인덱싱, 삭제 처리 등)** 가 백엔드에서 어떻게 구현되고 작동하는지 상세히 기술한 테크니컬 문서입니다.

---

## 1. 📤 무중단 업로드 파이프라인 (Upload)
**[핵심 라우터]:** `api/routers/upload.py`

*   **동작 방식:**
    1.  스마트폰이나 브라우저에서 다중 파일을 비동기(FormData) 형태로 전송합니다.
    2.  서버 메모리가 폭발하지 않도록, 들어오는 즉시 청크(Chunk) 라인 단위로 읽어 디스크의 `app/data/uploads_raw/` 라는 대기열(Queue) 전용 임시 폴더에 파일 포맷 그대로 쏟아 놓습니다.
    3.  파일 수신이 모두 완료되면 프론트엔드에 즉각 `200 OK`를 리턴하여 **모바일 화면이 멈추거나 튕기는 현상을 원천 방어(Zero-Blocking)** 합니다.
    4.  그 직후 FastAPI의 `BackgroundTasks` 트랙을 점화시켜, Celery 워커에 작업을 비동기로 통보합니다.

## 2. 🗃️ 시계열 폴더 정리 및 찌꺼기 청소 (Organizer Pipeline)
**[핵심 라우터 모듈]:** `api/routers/organizer.py`

*   **동작 방식:**
    1.  `uploads_raw/` 에 대기 중인 파일들을 한꺼번에 메모리에 올리지 않고 VRAM 오버플로우 방지를 위해 **200장 단위(Batch)** 로 쪼개어 프로세싱을 시작합니다.
    2.  **Junk 필터링 (Hash 검사):** `organizer_state.db`에 저장된 이전 파일들의 해시값과 대조하여 복제된 사본을 발견 즉시 영구 파기시킵니다.
    3.  **메타데이터 추출 (EXIF):** 남은 사진에서 EXIF 데이터를 까서 `Date(촬영일자)` 와 `GPS(위경도)` 를 추출합니다.
    4.  **표준 한국어 역추적 지오코딩 (Nominatim KO):**
        - 추출된 GPS 좌표를 OpenStreetMap API(`language='ko'`)에 던집니다.
        - **"[국가/도]-[도시/구]"** 형태의 완벽한 100% 한글 표준 명칭(예: `미국-호놀룰루`, `경기도-성남시`) 만을 반환받습니다. (실패 시 "위치정보없음" 부여)
    5.  **디렉토리 트리 안착 연산 및 이름 충돌 방어:**
        - `{Date}_{Location}` 정규 폴더(예: `2019/2019-03_경기도-성남시/`)를 자동 생성하고 파일명 일련번호 충돌 무결점 방어 후 `shutil.move` 합니다.

## 3. 🌌 다중 딥러닝 벡터 스캐너 (Vector Indexer)
**[핵심 엔진 모듈]:** `api/services/indexer/orchestrator.py` 및 파생 컴포넌트들(`model_florence`, `model_faces`, `model_siglip`)

*   **동작 방식:** 폴더 정리가 끝난 직후 **Redis/Celery 체인**에 의해 바로 배턴 터치를 받아 분리 가동되는 심층 스캐너입니다.
    1.  **배치 프로세싱 & 리스캔 방지:** 디렉토리를 싹 훑은 다음, Qdrant에 값이 살아있는 파일 철저히 패스.
    2.  **다중 모델 컨베이어 벨트:** 
        - **InsightFace:** 이미지 속 가족 얼굴 위치와 특징점(512D) 추출
        - **HSEmotion:** 추출된 얼굴 표정 텍스트 할당
        - **Florence-2-base:** 영문 캡션 및 객체 생성 (`bfloat16` 정밀도. 토큰 오버플로우 제한 패치 적용)
        - **SigLIP:** 분위기 및 인물 고밀도 벡터 공간(768D) 압축
    3.  **VRAM 스파이크 방어:** 4개의 거대 모델이 VRAM(8GB) 안에서 터지지 않도록, **BATCH_SIZE 10장 단위 직렬 메모리 캡슐 구조**로 동작합니다.
    4.  **마스터 사전(Dictionary) 자동 교체:** 루프를 돌며 발견된 모든 지역명칭들을 취합하여, Gemini 파서 엔진을 위한 `/app/data/available_tags.json` 사전에 자가 업데이트 (Self-Healing).

## 4. 🪦 3단 연속 하드 딜리트 파이프라인 (Hard Delete)
**[핵심 라우터]:** `api/routers/remove.py`

*   **동작 방식:** 스마트폰에서 휴지통 아이콘을 누르면 발동하는 3중 파괴 체인
    1.  **File System 1차 소각:** 실제 원본 파일 및 메타 XMP 파일 삭제. 더 나아가, 잔류하기 쉬운 **고속 로딩용 파생 썸네일 파일(`.webp`)**을 정확히 색출하여 동반 파기.
    2.  **Vector Store 2차 소각:** Qdrant DB 포인트 삭제.
    3.  **Local DB 3차 묘비 세우기:** SQLite `vectorized_files` 레코드에 강제로 `DELETED` 상태 각인. 이후 인덱서가 캐시를 재조회하더라도 인위적으로 버린 파일임을 인증받고 부활 차단.

## 5. 🧬 자율 진화 피드백 시스템 v2.0 (Self-Healing Feedback & Clean Re-Build)
**[핵심 비즈니스 모듈]:** `api/services/feedback_service.py` 와 `api/tasks.py` (Celery)

*   **동작 방식 (1:N 시각 군집 확장 및 무결점 리인덱싱):** 사용자가 누락된 미분류 정보(Unknown)를 1장만 채워주면, AI가 일괄 교정하는 시스템입니다.
    1.  **단일 질의 및 시각 군집화:** 1장의 사진을 교정하면, 거리가 가까운 유사 군집 N장이 자동 색출 타겟으로 포착됨.
    2.  **결손 데이터 1/N 무작위 등확률 선별:** Location 편향 버그를 고쳐 Date, Location 누락 시 동등하게 1/N 체계로 출제함.
    3.  **100% 무결점 클린 파기 후 ExifTool 주입:** 타겟이 된 사진의 모든 과거 DB 찌꺼기와 XMP를 날리고, `exiftool` 로 하드코딩 후 폴더 이주.
    4.  **🚨 Enterprise Redis Celery 비동기 메시지 대기열 큐 (Single-Concurrency):** 
        - **(문제점 방어):** 수십 번의 피드백 연타 시 파일 이동 `shutil.move`의 동시성 접근 불가 `FileNotFoundError` 발생 방어.
        - **(엔터프라이즈 솔루션 구현):** FastAPI 라우터는 기다리지 않고 **Redis 큐에 `.delay()`** 명령어만 발급. `celery_worker` 컨테이너가 1개의 단일 스레드로(Single Concurrency) 순서대로 뽑아먹으며, `organizer`와 `indexer` 시스템을 차분히 연쇄 구동시킴.
        - **(VRAM 무결화):** 이 Celery 워커는 `max_tasks_per_child=1` 옵션을 가져서 작업이 끝나는 순간 프로세스를 자살시켜 **PyTorch GPU 메모리를 강제 VRAM 0%로 완벽하게 비워주는 초강력 안전 장치** 임무를 수행함.

---

## 6. 📸 자연어 하이브리드 검색 엔진 (Search Architecture)
**[핵심 라우터]:** `api/routers/search.py`

사용자가 검색창에 "우리 가족이 하와잌 해변가에서 노는 거 보여줘"라고 자연어로 요청했을 때 작동하는 4단계 지능형 검색 기어입니다.

1. **마스터 사전을 참고하는 LLM 정밀 파싱 (Gemini)**
   - `["가족 이름 맵핑"]`, `["미국-하와이"]` 등 오타 보정 후 마스터 사전 내부 값과 정밀 대조.
   - **[할루시네이션(환각) 억제]**: 사전에 없는 완전한 타 지역(알래스카) 검색 시, 뇌피셜로 지어내지 않고 기계적으로 `""(빈 값)`을 반환하여 잘못된 시공간 추론 무력화.
2. **철통 방어 1차 수문장 (Must Condition)**: 인물과 장소를 1차 필터링 교집합으로 100% 커팅.
3. **무한 탐색 벡터 검색 (가중치 70%)**: 영문 장면 묘사(Scene)를 768D 공간에서 탐색.
## 7. 📁 API 폴더 구조 및 모듈 설명 (Clean Architecture)
이 시스템은 "관심사의 분리(Separation of Concerns)" 원칙에 따라, 스파게티 형태였던 단일 파일들을 `api/` 디렉토리 아래 각각의 전문 도메인(Domain)으로 완전히 해체하여 관리합니다.

```text
📁 api/
 ┣ 📂 routers/ (API 통신을 주고받는 접객 담당 최전선 앤드포인트 모음)
 ┃ ┣ 📄 facelearn.py: 얼굴 특징 벡터 추출 및 학습 트리거
 ┃ ┣ 📄 feedback.py: 사용자의 1:N 수정 지시를 받아 Redis 대기열 큐로 즉시 넘기는 임무
 ┃ ┣ 📄 organizer.py: 업로드 찌꺼기 파일 제거 및 한글 트리 분류 작업
 ┃ ┣ 📄 photo.py: 디스크에서 특정 사진 이미지/WebP 바이너리를 가져와 렌더링
 ┃ ┣ 📄 remove.py: 스마트폰에서 삭제 버튼 터치 시 Qdrant와 하드디스크 100% 완전 파기
 ┃ ┣ 📄 search.py: Gemini LLM이 파싱한 검색어를 넘겨받아 Qdrant에서 벡터를 탐색
 ┃ ┣ 📄 upload.py: 프론트엔드 비동기 멀티파트 파일을 받아 `uploads_raw` 대기열에 임시 안착시킴
 ┃ ┣ 📄 vectorindexer.py: Qdrant에 이미지를 넣어 인덱싱하는 비동기 트리거
 ┃ ┗ 📄 views.py: HTML 템플릿(frontend/index.html) 서빙
 ┃
 ┣ 📂 services/ (실제로 무거운 비즈니스 로직과 딥러닝 연산을 수행하는 공장 라인)
 ┃ ┣ 📂 daemons/ (과거에 사용되던 SQLite 무한 폴링 큐. 현재는 Redis Celery로 대체되며 소각됨)
 ┃ ┣ 📂 indexer/ (안면, 감정, 분위기, 캡션 AI 모델 4황 탑재 딥러닝 코어 공장)
 ┃ ┃ ┣ 📄 model_faces.py: InsightFace + HSEmotion 분석 전담 함수
 ┃ ┃ ┣ 📄 model_florence.py: Florence-2 모델 OOM 방어 및 Bfloat16 생성 함수
 ┃ ┃ ┣ 📄 model_siglip.py: SigLIP 768D 이미지 특성 추출 병합 함수
 ┃ ┃ ┣ 📄 orchestrator.py: 위 3개 모델 공장을 순서대로 가동시키는 통합 지휘관 패러다임
 ┃ ┃ ┣ 📄 progress_tracker.py: `progress.json` 출력으로 프론트엔드 프로그레스 바 연동
 ┃ ┃ ┗ 📄 qdrant_store.py: 추출된 Payload + Vector를 Qdrant DB 체계에 안전하게 Upsert
 ┃ ┃
 ┃ ┗ 📄 feedback_service.py: 사용자가 준 피드백을 ExifTool에 하드코딩시키고 물리적 1:N 튜닝 처리
 ┃
 ┣ 📂 utils/ (공용 도구 모음)
 ┃ ┗ 📄 metadata.py: XMP 사이드카(.xmp 파일)를 자동 생성하거나 읽어오는 스크립트 모음
 ┃
 ┗ 📄 tasks.py: `celery_worker` 컨테이너가 실행할 Redis Celery 통합 레지스트리 (모든 무거운 도메인 함수의 `@celery_app.task` 명찰 부착소)
```
