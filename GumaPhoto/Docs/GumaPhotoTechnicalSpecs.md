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
    3.  **메타데이터 추출 (EXIF Base):** 남은 사진에서 EXIF 데이터를 까서 `Date(촬영일자)` 와 `GPS(위경도)` 를 기초 추출합니다.
    4.  **디렉토리 트리 안착 연산 및 이름 충돌 방어:**
        - `{Date}_{Location}` 정규 폴더(예: `2019/2019-03/`)를 자동 생성하고 이름 충돌 무결점 방어(`연-월_0001` 순차 UUID 방식)를 거친 후 `shutil.move` 합니다. (현재 폴더 이름은 더 이상 메타데이터 파싱의 기준이 되지 않고, 오직 물리적 보관의 형태소로서만 작용합니다.)

## 3. 🌌 다중 딥러닝 벡터 스캐너 (Vector Indexer)
**[핵심 엔진 모듈]:** `api/services/indexer/orchestrator.py` 및 파생 컴포넌트들(`model_florence`, `model_faces`, `model_siglip`)

*   **동작 방식:** 폴더 정리가 끝난 직후 **Redis/Celery 체인**에 의해 바로 배턴 터치를 받아 분리 가동되는 심층 스캐너입니다.
    1.  **배치 프로세싱 & 지오코딩 캐시(OSM):** 디렉토리를 싹 훑은 다음, EXIF의 위경도를 Qdrant로 포워딩합니다. 이때 **OSM 역 지오코딩(Nominatim)**을 인덱서 내부에서 직접 호출하며 110m 묶음 해시 캐싱 전략을 통해 글로벌 오버리미트를 방어합니다.
    2.  **프론트엔드 최적화 (WebP):** GPU 배치 연산을 대기하는 동안 무거운 원본 이미지를 `(300, 300)` `.webp` 썸네일로 즉각 컴파일하여 디스크에 자동 배치합니다.
    3.  **다중 모델 컨베이어 벨트:** 
        - **InsightFace:** 이미지 속 가족 얼굴 위치와 특징점(512D) 추출 (나이에 따른 다기 분기 `준우_1` 등은 `split('_')` 로직으로 백엔드에서 정규 본명으로 튜닝 흡수)
        - **HSEmotion:** 추출된 얼굴 표정 텍스트 할당
        - **Florence-2-base:** 영문 캡션 및 객체 생성 (`bfloat16` 정밀도. 토큰 오버플로우 제한 패치 적용)
        - **SigLIP:** 분위기 및 인물 고밀도 벡터 공간(768D) 압축
    4.  **VRAM 스파이크 방어:** 4개의 거대 모델이 VRAM(8GB) 안에서 터지지 않도록, **BATCH_SIZE 10장 단위 직렬 메모리 캡슐 구조**로 동작합니다.
    5.  **마스터 사전(Dictionary) 자동 교체:** 루프를 돌며 발견된 모든 지역명칭들을 취합하여, Gemini 파서 엔진을 위한 `/app/data/available_tags.json` 사전에 자가 업데이트 (Self-Healing).

## 4. 🪦 3단 연속 하드 딜리트 파이프라인 (Hard Delete)
**[핵심 유틸리티]:** `api/utils/photo_purger.py` (라우터는 `api/routers/delete.py`)

*   **동작 방식:** 스마트폰에서 휴지통 아이콘을 누르거나 피드백 과정에서 파생 데이터를 파기할 때 공통으로 발동하는 3중 파괴 체인
    1.  **File System 1차 소각:** 실제 원본 파일 및 메타 XMP 파일 삭제. 더 나아가, 잔류하기 쉬운 **고속 로딩용 파생 썸네일 파일(`.webp`)**을 정확히 색출하여 동반 파기. (단, 피드백의 경우 `keep_original=True` 플래그로 원본만 무사히 보존)
    2.  **Vector Store 2차 소각:** Qdrant DB 벡터 포인트 즉각 삭제.
    3.  **Local DB 3차 묘비 세우기:** SQLite 마스터 장부 마킹. 삭제 시에는 즉각 `DELETED` 상태를 각인하여 AI 인덱서가 캐시를 재조회하더라도 인위적으로 버린 파일임을 인증받고 유령(Zombie) 부활을 원천 차단.

## 5. 🧬 자율 진화 피드백 시스템 v2.0 (Self-Healing Feedback & Clean Re-Build)
**[핵심 비즈니스 모듈]:** `api/services/feedback_service.py` 와 `api/tasks.py` (Celery)

*   **동작 방식 (1:N 시각 군집 확장 및 무결점 리인덱싱):** 사용자가 누락된 미분류 정보(Unknown)를 1장만 채워주면, AI가 일괄 교정하는 시스템입니다.
    1.  **단일 질의 및 시각 군집화:** 1장의 사진을 교정하면, 거리가 가까운 유사 군집 N장이 자동 색출 타겟으로 포착됨. (**WebP 썸네일 고속 렌더링 도입**: 프론트엔드의 체크박스 레이어에서 무식하게 원본 JPG(수십MB)를 내리지 않고 `_jpg.webp` 등 최적화된 저해상도 경로를 파싱/로드 후 우회하여 VRAM과 트래픽 부담 한계를 타파).
    2.  **결손 데이터 1/N 무작위 등확률 선별:** Location 편향 버그를 고쳐 Date, Location 누락 시 동등하게 1/N 체계로 출제함.
    3.  **100% 무결점 클린 파기 후 ExifTool 주입:** 타겟이 된 사진의 모든 과거 DB 찌꺼기와 XMP를 `PhotoPurger`로 날리고, 독립 모듈인 `MetadataEditor`를 통해 하드코딩한 후 `uploads_raw` 폴더로 이주. (이 과정에서 기존의 허술했던 폴더명 기반 파싱을 폐기하고, 오롯이 **물리적 Exif 메타데이터와 Qdrant Payload 간의 Source of Truth 동기화** 체계 개편을 완료).
    4.  **Audit Logs (블랙박스) 실시간 감시망:** 물리적인 변화를 가스라이팅하거나 속일 수 없도록, Qdrant 및 디스크의 진위(Before vs After) 상태와 추적 Trace ID, 최종 Exif를 무조건 `audit_trace.json`에 영속 기록하여 시스템 메뉴 모달에서 사용자가 100% 투명하게 영수증 검사를 할 수 있는 무결성 아키텍처 지원.
    5.  **🚨 Enterprise Redis Celery 비동기 메시지 대기열 큐 (Single-Concurrency):** 
        - **(문제점 방어):** 수십 번의 피드백 연타 시 파일 이동 `shutil.move`의 동시성 접근 불가 `FileNotFoundError` 발생 방어. (최근 파이썬 `json` 모듈 로컬-글로벌 섀도잉 중복 버그로 N장 중 1장만 먹히던 최악의 에러마저 완전 적출 승리).
        - **(엔터프라이즈 솔루션 구현):** FastAPI 라우터는 기다리지 않고 **Redis 큐에 `.delay()`** 명령어만 발급. `celery_worker` 컨테이너가 1개의 단일 스레드로(Single Concurrency) 순서대로 뽑아먹으며, `organizer`와 `indexer` 시스템을 차분히 연쇄 구동시킴.
        - **(VRAM 무결화):** 이 Celery 워커는 `max_tasks_per_child=1` 옵션을 가져서 작업이 끝나는 순간 프로세스를 자살시켜 **PyTorch GPU 메모리를 강제 VRAM 0%로 완벽하게 비워주는 초강력 안전 장치** 임무를 수행함.

---

## 6. 📸 자연어 하이브리드 검색 엔진 (Search Architecture)
**[핵심 라우터]:** `api/routers/search.py`

사용자가 검색창에 "우리 가족이 하와잌 해변가에서 노는 거 보여줘"라고 자연어로 요청했을 때 작동하는 4단계 지능형 검색 기어입니다.

1. **마스터 사전을 참고하는 LLM 정밀 파싱 (Gemini)**
   - `["가족 이름 맵핑"]`, `["미국-하와이"]` 등 오타 보정 후 마스터 사전 내부 값과 정밀 대조.
   - **[오타 보정 알고리즘]**: 사용자가 "글랜데일"이라고 치더라도 `difflib.get_close_matches` 알고리즘을 통해 마스터 사전 내의 "글렌데일"과 Fuzzy 매칭 시켜 AI 번역 결과를 스스로 교정함.
   - **[할루시네이션(환각) 억제]**: 사전에 없는 완전한 타 지역(알래스카) 검색 시, 뇌피셜로 지어내지 않고 기계적으로 `""(빈 값)`을 반환하여 잘못된 시공간 추론 무력화.
2. **철통 방어 1차 수문장 (Must Condition)**: 인물과 장소를 1차 필터링 교집합으로 100% 커팅.
3. **무한 탐색 벡터 검색 (가중치 70%)**: 영문 장면 묘사(Scene)를 768D 공간에서 탐색.

## 7. ⚙️ 프론트엔드 모바일 PWA 및 렌더링 최적화 
1. **Web Share API Level 2 (Blob Fetching)**
   - 브라우저 특성상 `navigator.share()` 로 이미지를 보내면 보안상 URL String만 카카오톡에 전송되는 치명적 문제를 해결하기 위해, 프론트엔드가 이미지 `src`를 백그라운드 Fetch로 빨아들여 물리적인 바이너리 `Blob`에서 `File` 객체로 포맷 형변환 후 네이티브 OS 전송 시트(Native Share Sheet)에 강제 주입함. 이를 통해 내부망(Private) 외부에서도 언제든 원본 사진 파일을 이격 공유 가능.
2. **터치 이벤트 하이재킹 방어 (iOS Haptic/Lift 무효화)**
   - 아이폰(Safari)의 사진을 꾹 누를 때 발생하는 시스템 기본 드래그 앤 드롭 프론트뷰(Lift 현상)나 영역 탭 하이라이트를 완전히 무력화(`-webkit-user-drag: none;`)하여, CSS로 그려둔 `border-radius` 둥근 모서리가 확대축소 연산 중에도 절대 파괴되지 않게 보호함. 또한 `Panzoom.js` 핀치 줌 라이브러리와 조합하여 순정 Photos 앱의 1티어 조작감을 완벽 재현함.
3. **Cloudflare & Edge 정적 캐시(Static Cache) 무결점 무효화 우회**
   - CDN(Cloudflare)이나 브라우저의 끈질긴 HTML/JS 파일 해싱 캐시 정책 때문에 `?v=XXX` 쿼리 파라미터 강제 패치가 무시되는 치명적 현상을 방어합니다. DOM 노드(HTML)가 낡은 뼈대로 렌더링되더라도, 자바스크립트가 실행될 때 부모 노드 유효성을 100% 검사해 강제로 올바른 위치에 DOM을 납치(Hijack)하여 재생성합니다.
   - 지속적인 Edge 서버 캐싱 오작동을 무력화하기 위해, 주요 JS 에셋 자체의 파일명을 교체(`script_app.js`, `guma-earth_app.js`)하는 초강수로 완전 무결점의 즉각 배포(Immediate Deployment) 파이프라인을 확립했습니다.

## 8. 📁 API 폴더 구조 및 모듈 설명 (Clean Architecture)
이 시스템은 "관심사의 분리(Separation of Concerns)" 원칙에 따라, 스파게티 형태였던 단일 파일들을 `api/` 디렉토리 아래 각각의 전문 도메인(Domain)으로 완전히 해체하여 관리합니다.

```text
📁 api/
 ┣ 📂 routers/ (API 통신을 주고받는 접객 담당 최전선 앤드포인트 모음)
 ┃ ┣ 📄 facelearn.py: 얼굴 특징 벡터 추출 및 학습 트리거
 ┃ ┣ 📄 feedback.py: 사용자의 1:N 수정 지시를 받고 Gemini로 문맥을 파악한 뒤 Redis 대기열 큐로 즉시 넘기는 임무
 ┃ ┣ 📄 organizer.py: 업로드 찌꺼기 파일 제거, 한글 트리 분류 및 유령 깡통 폴더 후처리(`os.rmdir`) 작업
 ┃ ┣ 📄 photo.py: 디스크에서 특정 사진 이미지/WebP 바이너리를 가져와 렌더링
 ┃ ┣ 📄 delete.py: 스마트폰에서 삭제 버튼 터치 시 HTTP 요청을 해석하여 `PhotoPurger` 유틸리티를 호출
 ┃ ┣ 📄 search.py: Fuzzy(근사치) 오타 허용 알고리즘과 Gemini LLM이 파싱한 검색어를 넘겨받아 Qdrant에서 벡터 조인 탐색
 ┃ ┣ 📄 upload.py: 프론트엔드 비동기 멀티파트 파일을 받아 `uploads_raw` 대기열에 임시 안착시킴
 ┃ ┣ 📄 vectorindexer.py: Qdrant에 이미지를 넣어 인덱싱하는 비동기 트리거
 ┃ ┗ 📄 views.py: HTML 템플릿(frontend/index.html) 서빙
 ┃
 ┣ 📂 services/ (실제로 무거운 비즈니스 이벤트/통신/API 로직 등을 조율하는 오케스트레이터 공장)
 ┃ ┣ 📂 daemons/ (과거에 사용되던 SQLite 무한 폴링 큐. 현재는 사라짐)
 ┃ ┣ 📂 indexer/ (안면, 감정, 분위기, 캡션 AI 모델 4황 탑재 딥러닝 코어 공장)
 ┃ ┃ ┣ 📄 model_faces.py: InsightFace + HSEmotion 분석 전담 함수
 ┃ ┃ ┣ 📄 model_florence.py: Florence-2 모델 OOM 방어 및 Bfloat16 생성 함수
 ┃ ┃ ┣ 📄 model_siglip.py: SigLIP 768D 이미지 특성 추출 병합 함수
 ┃ ┃ ┣ 📄 orchestrator.py: 위 3개 모델 공장을 순서대로 가동시키는 통합 지휘관 패러다임
 ┃ ┃ ┣ 📄 progress_tracker.py: `progress.json` 출력으로 프론트엔드 프로그레스 바 연동
 ┃ ┃ ┗ 📄 qdrant_store.py: 추출된 Payload + Vector를 Qdrant DB 체계에 안전하게 Upsert
 ┃ ┃
 ┃ ┗ 📄 feedback_service.py: 피드백 타겟을 모아 `PhotoPurger`와 `MetadataEditor`에 하청을 주고 완료 후 `publish_event` 릴레이 통신을 발사하는 총괄 지휘자
 ┃
 ┣ 📂 utils/ (순수 무상태(Stateless) 독립형 범용 도구 모음)
 ┃ ┣ 📄 metadata_editor.py: ExifTool 지오코딩 및 메타데이터 하드코딩 주입 전담기
 ┃ ┣ 📄 photo_purger.py: 3대 데이터(SQLite, XMP/WEBP, Qdrant) 일괄 파기 및 무결점 증발 전담 청소기
 ┃ ┗ 📄 metadata.py: XMP 사이드카를 자동 생성하거나 읽어오는 고속 스크립트 모음
 ┃
 ┗ 📄 tasks.py: `celery_worker` 컨테이너가 실행할 Redis Celery 통합 레지스트리 (모든 무거운 도메인 함수의 `@celery_app.task` 명찰 부착소)

 📁 Scripts/ (서버 관리자용 유틸리티 및 오프라인 전처리 툴)
  ┣ 📄 factory_reset_db.py: 데이터베이스 구조계(Qdrant/SQLite)를 즉시 소각하여 VRAM 오염과 싱크를 100% 멸균 초기화하는 스크립트.
  ┗ 📄 preprocess_tool.py: 업로드 파이프라인 진입 전, 사진별로 카카오맵 좌표를 수동으로 정확히 태깅하여 Exif Date/GPS를 선-주입(Pre-injection)하는 정밀 타격 툴.

 📁 tool/exiftool_engine/ (모듈 내재화)
  ┗ 📦 외부 의존성 설치 문제나 PATH 환경 변수에 기대지 않도록, 완전 독립형(Standalone) Perl ExifTool 배포판을 폴더 내부에 삽입하여 영구적인 캡슐화 작동 보장.
```
