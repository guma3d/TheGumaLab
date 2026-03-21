# 🚀 GumaPhoto 개발자 온보딩 가이드 (시작하기 전에 반드시 읽어주세요)

GumaPhoto 프로젝트에 오신 것을 환영합니다!
이 프로젝트는 단순한 갤러리를 넘어, 멀티모달 AI(SigLIP, Florence-2, InsightFace, HSEmotion)와 LLM(Gemini)이 결합된 **최첨단 지능형 가족 특화 갤러리 검색 시스템**입니다.

본격적인 코딩 및 유지보수 작업에 들어가기 앞서, 시스템이 어떤 철학으로 설계되었는지 완벽하게 파악하기 위해 아래의 **3대 핵심 아키텍처 문서**를 반드시 순서대로 정독해 주시기 바랍니다.

## 📖 1. 필수 정독 문서 (Core Documentation)

1. **[GumaPhotoPlan.md](./Docs/GumaPhotoPlan.md) (프로젝트 마스터 플랜)**
   - 프로젝트의 궁극적 목표, 현재 완료된 로드맵 단계, 그리고 핵심 인프라 구축의 큰 그림을 설명합니다. (전체 숲을 보는 용도)
2. **[GumaPhotoTechnicalSpecs.md](./Docs/GumaPhotoTechnicalSpecs.md) (모듈별 핵심 기술 명세서 및 아키텍처)**
   - 앱 내부에서 5대 코어 프로세스(업로드, 폴더정리, 벡터인덱싱, 검색엔진, 삭제처리)가 어떻게 작동하고 통합 DB(SQLAlchemy)와 연동되어 예외를 처리하는지 기술적인 명세서를 담고 있습니다. 
3. **[GumaPhotoProgress.md](./Docs/GumaPhotoProgress.md) (프로젝트 진행 상황 및 기술 트러블슈팅 내역)**
   - 과거부터 지금까지 어떤 기술적 난관이 있었으며 그 문제들을 어떤 논리와 코드로 해결해 왔는지 상세한 개발 히스토리가 기록되어 있습니다. (버그 방지 및 레거시 파악용)

---

## 📂 2. 완벽하게 압축된 디렉토리 구조 (Clean Architecture)

본 시스템은 극도로 정돈된 마이크로서비스 형태의 클린 아키텍처를 유지합니다. 어지러운 테스트 스크립트나 루트 폴더 오염은 절대 금지됩니다.

*   `📁 GumaPhoto/` (Root)
    *   **핵심 뼈대 파일만 존재합니다.**
    *   `main.py`: FastAPI 백엔드 API 라이프사이클 관리 및 라우터 주입, SQLAlchemy DB 엔진 동기화(`Base.metadata.create_all`)
    *   `docker-compose.yml`: Redis, Celery, Qdrant 등 메시지 브로커와 AI DB 묶음 체인
    *   `Starting.md` 등 온보딩 가이드, `.env`, `requirements.txt`
*   `📁 core/` (핵심 공통 데이터베이스 및 상태)
    *   `database.py`: SQLAlchemy 연결 엔진 및 세션 관리자(`SessionLocal`)
    *   `models.py`: 통합 마스터 피스 DB 클래스 모델(`Photo`) 설계도
    *   `state.py`: 런타임 전역 변수 스테이트 저장소
*   `📁 api/` (Domain-Driven API & Services)
    *   `routers/`: `upload`, `search`, `organizer`, `feedback`, `delete` 등 주제별로 완전히 쪼개진 FastAPI 엔드포인트 모음.
    *   `services/`: `indexer/` (AI 딥러닝 엔진룸), `feedback_service.py` (조율 및 비즈니스 로직) 등 중(Heavy) 처리 모듈.
    *   `utils/`: `photo_purger.py`, `metadata_editor.py` 등 범용 무상태(Stateless) 도구.
    *   `tasks.py`: Celery 비동기 큐 작업 레지스트리 (Redis 연동).
*   `📁 frontend/` (정적 파일 및 UI 에셋)
    *   앱의 시각을 담당하는 `style.css`, 인텔리전트 프론트엔드 라우팅 `script.js` 및 UI 에셋 모음.
*   `📁 Docs/`
    *   플랜, 진행 상황, 기술 명세서(Architecture) 등 코어 기술 관련 Markdown 문서 전용 보관소.

---

## 🛡️ 3. 개발 5대 원칙 및 코드 작성 룰 (The Golden Rules)

> **[규칙 1. 원본 무결성 유지]**
> 어떠한 로직 개편이 있더라도, 사용자의 **원본 사진 및 내부 EXIF 메타데이터는 1%도 훼손되거나 조작되어서는 안 됩니다.** 데이터 무결성이 최우선입니다. 

> **[규칙 2. 문서 자기 주도 업데이트 엄수 (Self-Healing Docs)]**
> 변경사항이 발생하면 관련된 모든 Markdown 문서를 스스로 먼저 스캔하여 즉시 최신 내용으로 동기화(업데이트) 해두어야 합니다.

> **[규칙 3. 100% 롤백 보장 기조 (Zero-Risk Commit)]**
> 오류가 발생했을 때 언제든지 단 몇 초 만에 이전 상태로 안전하게 롤백(Rollback) 할 수 있는 안정성 버퍼를 항시 확보해 두어야 합니다.

> **[규칙 4. 마이크로서비스 모듈화 (Domain-Driven API) 준수 강력 권고]** 🚨
> 새로운 기능을 추가하거나 기존 로직을 수정할 때, 거대한 단일 스크립트에 잡다한 기능을 때려 박는 스파게티성 코딩을 엄격히 금지합니다. 반드시 `api/routers/` 내의 해당 분야 라우터 모듈(예: search, upload, organizer)에 API 엔드포인트를 매핑하고, 실제 무거운 AI 연산이나 복잡한 비즈니스 로직은 `api/services/` 의 독립된 컴포넌트로 분리 배치하십시오.

> **[규칙 5. 통합 ORM DB 스키마 준수 (Single Source of Truth)]** 🚨
> `upload`, `remove`, `vectorindexer` 등 어떠한 파이프라인에서 작업하든, 사진의 상태를 기록하거나 찾을 때 절대로 쌩(Raw) SQLite 쿼리(`sqlite3.connect()`)나 새로운 테이블을 파편화시켜 생성하지 마십시오. 
> 반드시 **`core.models.Photo`** 모듈에 정의된 **SQLAlchemy ORM 단일 객체를 로드**하여 작업해야 합니다.
> - 데이터 중복 및 기입 누락 방지를 위해, 우리가 정규화 해둔 파라미터 규격명(`filepath`, `file_hash`, `width`, `height`, `file_size_bytes` 등)을 철저히 준수하여 값을 기입(`add()`) 하거나 갱신(`commit()`) 하십시오.
> - 파일의 **생애주기 이력(Lifecycle) 추적**은 오직 **`status` 단일 컬럼 변경 (`UPLOADED` -> `ORGANIZED` -> `VECTORIZED` -> `DELETED`)** 이라는 깔끔한 상태머신(State Machine) 방식으로만 통제하여 DB의 완전한 무결성을 지켜내야 합니다.

> **[규칙 6. 마일스톤 달성 시 즉각적인 깃허브 푸시 (Continuous GitHub Sync)]** 🚨
> 의미 있는 리팩토링이나 새로운 기능 구조가 컨테이너에서 정상적으로 구동됨이 확인되었다면, 작업을 멈추지 말고 즉각적으로 프로젝트 루트의 `sync_github.ps1` 스크립트를 가동(또는 `/sync_github` 워크플로우 실행)하여, 코드가 유실되지 않도록 **반드시 원격 GitHub 저장소에 영구 보존(Commit & Push)** 해야 합니다.
