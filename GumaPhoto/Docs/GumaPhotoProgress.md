# GumaPhoto 프로젝트 진행 상황 (Progress Log)

이 문서는 GumaPhoto 서비스의 개발 진행 상황과 중요 테스트/기술 결정 내역을 기록하는 공간입니다.

## 📌 [1단계] 인프라 및 기본 구조 셋업 세팅 (완료)
*   **Docker 및 FastAPI 구축:** 포트 매핑 및 Reverse Proxy 설정 완료.
*   **파일 시스템(Clean Architecture) 재정렬:** 어지럽게 분산되어 있던 50여 개의 진단 스크립트를 용도에 맞게 분리 및 영구 폐기.

## 📌 [2단계] 맞춤형 안면 인식 패러다임 점검 (완료)
*   **모델 업그레이드:** 오픈소스 최고 권위 `InsightFace(buffalo_l)` 및 PyTorch 시간차 경량화 표정 엔진 `HSEmotion`으로 전격 세대교체 달성.

## 📌 [3단계] 갤러리 물리적 정리 및 파이프라인 고도화 (완료)
*   **충돌 방어 (Collision):** 베이스 네임 일치 시 뒷번호 밀어넣기(Hole-Filling) 방어 세팅 완료.
*   **글로벌 한글 강제 매핑 (Geocoding-Ko):** OpenStreetMap 역추적 API에 `language='ko'`를 주입.
*   **쓰레기 필터 (Junk/Hash):** 스크린샷 찌꺼기와 완전 중복된 사진들 즉각 영구 삭제 로직.

## 📌 [4단계] 멀티모달 벡터 검색 및 캡셔닝 아키텍처 설계 (완료)
*   **다국어 SigLIP 768D + Florence-2 캡셔닝 융합:** 
    *   Florence-2 Bfloat16 캐주얼 정밀도로 구동 속도 극대화. 
    *   안정적인 **배치 10장** 처리 한계 설정 및 무한 루프 텍스트 환각 방어장치 (Repetition Penalty).
*   **태그 사전 자동 갱신 (Self-Healing Vocab):** 인덱서 돌입 후 `/app/data/available_tags.json` 마스터 사전에 자가 업데이트 실시.

## 📌 [5단계] AI 검색 엔진(LLM 파서)의 무결성 달성 (완료)
*   **환각(알래스카 할루시네이션) 원천 방어:** 빈 값 패스 로직을 발동시켜 아예 엉뚱한 장소로 창박해 내뱉는 Gemini의 지어내기(유추)를 철벽 통제.

## 📌 [6단계] 100% 완전 파기 묘비 (Hard Delete & Tombstone) (완료)
*   원본 사진, DB 페이로드, 그리고 파생 썸네일(`_heic.webp`) 바이너리까지 100% 물리 동반 파괴 적용. 
*   또한 이미 지워진 구 파일들이 유령처럼 부활하여 AI 엔진을 맴도는 것을 막기 위해 `status='DELETED'` 영구 사망 마크 각인 연계 완비.

## 📌 [7단계] 100% 무결점 피드백 자율 진화 시스템 v2.0 (완료)
*   **단일 사진 노출 포커싱:** 피드백 모달창에서 미분류 1장만을 직관적으로 노출시켜 편향 없는 1/n 무작위 수선 분배 구조 도출.
*   **ExifTool 주입 체계:** HEIC, MP4의 메타데이터를 100% 파싱 및 물리 하드코딩 업데이트 후 시스템 백지화(Re-build) 이주 처리 완료.

## 📌 [8단계] Premium SaaS UI/UX 전면 개편 (완료)
*   **초스무스 비동기 SPA 전환:** iOS 사파리 감성의 네이티브 액션 클립 및 글라스모피즘 탭 라우팅(`frontend/`) 개명. 랜더링 홀 부재 방어를 위한 10칸 무조건 슬라이더 보장 렌더 구성.

## 📌 [9단계] Enterprise 클린 모듈(Domain-Driven API) 아키텍처 (완료)
*   `vector_indexer.py`, `organizer_pipeline.py` 처럼 500줄이 넘어가던 모놀리식 뚱뚱한 코드 전체를 썰어 `api/routers/` (서빙 API) 와 `api/services/` (비즈니스 AI 공장) 내부의 파츠 6개로 쪼개고 완전히 분리 매핑 완료.
*   **Redis + Celery 로드 밸런싱 통제:** `worker_max_tasks_per_child=1` GPU 캐시 스왑을 강제 적용해 평생 무한히 사진을 구워도 PyTorch OOM 버그가 생기지 않는 기적 달성.

## 📌 [10단계] 전역 데이터베이스 단일 객체화 (SQLAlchemy ORM 도입) (완료)
*   **Raw SQLite 장부 전면 폐기:** 라우터와 인덱서 모듈 사방에 "INSERT OR REPLACE" 등 지저분하게 흩날리며 락다운 에러(DB is Locked)를 유발하던 낡은 하드코딩 쿼리를 영구 소각했습니다.
*   **단일의 객체 진실 공급원 (Single Source of Truth) 마련:** SQLite의 복잡한 테이블(`processed_files`, `vectorized_files` 등)을 뭉쳐내어, `core.models.py` 안에 **`Photo`** 라는 완벽한 마스터 객체 하나로 통합 설계했습니다.
    *   **정규 파라미터 매칭:** 사진 하나가 정리(Organize)될 때, 즉시 `width`, `height`, `file_size_bytes` 해상도 규격을 측정해 DB 객체에 미리 박아넣어, 추후 프론트엔드가 모바일 스크롤 잔상 현상(CLS) 없이 찰떡같이 렌더링되게 엮었습니다.
    *   **통합 Status 추적기:** 파편화 테이블 삭제 기록이 아닌, 단지 **`status='UPLOADED' -> 'ORGANIZED' -> 'VECTORIZED' -> 'DELETED'`** 속성 하나의 변경에 따라 시스템의 배턴 터치 흐름이 부드럽게 이어지는 극강의 OOP적 유지보수를 이룩했습니다.

## 📌 [11단계] 도메인 로직(Utils) 순수 분리 및 UI 버그 헌팅 (완료 🎯)
*   **`PhotoPurger` (데이터 말소 전담팀) 신설:** `delete.py` 및 피드백 모듈 내부에서 날것으로 굴러다니던 위험한 쓰레기 하드 딜리트(Qdrant, XMP, SQLite) 코드를 하나의 순수 유틸리티(Utility)로 100% 분리. `keep_original` 플래그 하나로 완전 파쇄 vs 피드백 보존을 마법처럼 통제 처리.
*   **`MetadataEditor` (Exif 전담팀) 신설:** 피드백이 내려찍히면 무지성으로 EXIF와 지오코딩만 수행하는 독립 모듈을 만들어 기존 거대 라우터를 수십 줄 다이어트 성공.
*   **프론트엔드 Scan 블로킹 오류 완벽 타파:** Qdrant 벡터 검색 시 자기 자신을 제외하거나 유사도 임계점 이하라서 화면이 먹통이 되던 버그를 고치기 위해, 타겟 백엔드에서 원본 사진 1장을 Index 0 에 무조건 강제 주입하도록 덮어씌움 처리.
*   **유령 깡통 폴더 영구 청소망 구축:** 피드백/삭제 메커니즘으로 인해 파일이 다 스왑되어 생기는 `2025-10` 같은 비어있는 고스트 폴더들을 오거나이저 동작 직후 `os.walk(topdown=False)` 로 가장 아랫바닥부터 훑으며 무자비하게 OS 단에서 삭제하도록 방어 로직 전개.
*   **풀-듀플렉스(Full-Duplex) 로깅 디스플레이 탑재:** Windows 사용자 친화적인 `View_Live_Logs.bat` 를 새롭게 개조하여, `gumaphoto_app` (FastAPI 통신망) 과 `celery_worker` (AI 기계실) 이 내뱉는 로그를 동일 프레임(터미널)에 시각적으로 태그를 붙여 통합 생중계 가능하도록 배포 완료.

## 📌 [12단계] 디테일 UX 고도화 및 네이티브 모바일 최적화 (완료 🎯)
*   **Web Share API Level 2 (물리적 파일 공유):** iOS/Android에서 사진 공유 시 단순 URL 텍스트가 전송되어 카카오톡 등에서 접근 권한 에러가 나던 현상을 타파. 클라이언트에서 Blob 데이터를 즉각 Fetch하여 `File` 객체로 물리적 패키징 후 네이티브 공유 시트에 던지는 방식으로 카카오톡 원본 직배송 완벽 호환 구현.
*   **PWA 및 네이티브 터치 블록(iOS 최적화):** 사파리의 고질적인 꾹 누르기 드래그(Lift) 효과나 하이라이트 발생 시 모서리 곡률(`border-radius`)이 날아가는 버그를 `-webkit-user-drag: none;` 단에서 완전 봉인.
*   **Pinch-to-Zoom 뷰어 탑재:** `Panzoom.js` 프레임워크를 이식하여 두 손가락 부드러운 줌인/아웃 구현 + 화면 단일 탭 시 거추장스러운 UI들만 스르르 사라지는(Fade 오파시티 토글) 영화 같은 몰입 뷰(Focus Mode) 완성.
*   **자동 고스트 롤백(Ghost Rollback) 방어 체계:** 사용자가 피드백 UI에서 동명이인이나 엉뚱한 인물로 잘못 태깅하고 재교정을 시도할 때, 구 폴더에 떨어져 있던 가짜 얼굴 크롭(`{point_id}.jpg`)을 `glob`로 글로벌 추적 후 원천 소각하는 롤백 메커니즘을 융합 완료.
*   **Windows 배치 스크립트 인코딩 가드:** 한글을 포함해 `chcp 65001` 선언 시 Windows `cmd.exe` 버그로 인해 `docker` 명령어나 변수가 바이트 밀림으로 잘리던 고질적 버그(`aphoto_app`)를 100% 영문 ASCII 변환을 통해 영구 해결.

## 📌 [13단계] 단일 진실 공급원(Qdrant) 아키텍처 완성과 독립 AI 모듈화 (완료 🎯)
*   **완벽한 Qdrant 단일화 (SQLite 완전 소각):** 피드백, 인덱서, 검색 등 모든 도메인에서 `SessionLocal`, `Photo` ORM 접근을 полностью 제거하여 파편화된 DB 동기화 오류를 원천 차단. 메타데이터와 벡터를 모두 품은 Qdrant 단일 생태계 확립.
*   **InsightFace 완전 독립 모듈화 (`InsightFaceModule`):** `vector_indexer`에 종속되어 있던 안면 인식 엔진을 `api/services/insightface_service.py`로 분리. 장소/날짜 피드백 시 불필요한 안면 분석을 생략(`skip_face=True`)할 수 있게 되어 Qdrant 덮어쓰기 파이프라인 속도가 비약적으로 상승.
*   **피드백 덮어쓰기(Overwrite) 메커니즘 전환:** 
    *   장소/날짜 피드백: 기존의 `PhotoPurger` 파쇄 후 `uploads_raw` 재업로드 큐를 타던 비효율적 롤백 방식에서 탈피하여, `MetadataEditor`로 EXIF를 영구 수정 후 즉시 Qdrant에 벡터를 덮어쓰도록(Overwrite) 진화.
    *   인물(얼굴) 피드백: 사용자가 명시적으로 선택한 1장의 사진만 `enrolled` 도감에 등록하고, 나머지 동반 선택된 타겟 사진들은 도감 오염 없이 `InsightFaceModule`로만 평가하여 Qdrant 페이로드를 즉각 업데이트하도록 초정밀 최적화 달성.
