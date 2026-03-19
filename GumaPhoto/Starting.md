# 🚀 GumaPhoto 개발자 온보딩 가이드 (시작하기 전에 반드시 읽어주세요)

GumaPhoto 프로젝트에 오신 것을 환영합니다!
이 프로젝트는 단순한 갤러리를 넘어, 멀티모달 AI(SigLIP, Florence-2, InsightFace, HSEmotion)와 LLM(Gemini)이 결합된 **최첨단 지능형 가족 특화 갤러리 검색 시스템**입니다.

본격적인 코딩 및 유지보수 작업에 들어가기 앞서, 시스템이 어떤 철학으로 설계되었는지 완벽하게 파악하기 위해 아래의 **4대 핵심 아키텍처 문서**를 반드시 순서대로 정독해 주시기 바랍니다.

## 📖 1. 필수 정독 문서 (Core Documentation)

1. **[GumaPhotoPlan.md](./GumaPhotoPlan.md) (프로젝트 마스터 플랜)**
   - 프로젝트의 궁극적 목표, 현재 완료된 로드맵 단계, 그리고 핵심 인프라 구축의 큰 그림을 설명합니다. (전체 숲을 보는 용도)
2. **[GumaPhotoSearchArchitecture.md](./GumaPhotoSearchArchitecture.md) (하이브리드 검색 아키텍처 및 작동 원리)**
   - "알래스카에서 노는 송이"를 검색했을 때, 앱 내부에서 Gemini LLM이 이를 어떻게 파싱하고, Qdrant 벡터 DB가 어떻게 SigLIP과 캡션을 섞어 리랭킹하는지 아주 상세한 수학적/논리적 작동 원리를 담고 있습니다. (핵심 검색 엔진 구조 파악용)
3. **[GumaPhotoProgress.md](./GumaPhotoProgress.md) (프로젝트 진행 상황 및 기술 결정 내역)**
   - 과거부터 지금까지 어떤 기술적 난관(중복 이름 처리, 썸네일 유령 파일 버그, 폴더 한국어 정식 명칭화 등)이 있었으며 그 문제들을 어떤 논리와 코드로 해결해 왔는지 상세한 개발 히스토리가 기록되어 있습니다. (버그 방지 및 레거시 파악용)
4. **[GumaPhotoTechnicalSpecs.md](./GumaPhotoTechnicalSpecs.md) (모듈별 핵심 기술 명세서)**
   - 시스템의 심장부를 구성하는 4대 코어 프로세스(업로드, 폴더정리, 벡터인덱싱, 완전삭제)가 내부적으로 어떠한 API와 로직을 통해 맞물려 돌아가는지 기능별 구현 원리가 상세히 적혀있습니다.

---

## 📂 2. 완벽하게 압축된 디렉토리 구조 (Clean Architecture)

저희 시스템은 극도로 정돈된 상태를 유지해야 합니다. 새로운 스크립트를 짤 계획이라면 반드시 아래의 폴더 룰을 따르십시오. Root 폴더는 메인 심장부에만 내어줍니다.

*   `📁 GumaPhoto/` (Root)
    *   **핵심 뼈대 파일만 존재합니다.**
    *   `main.py`: FastAPI 백엔드 API 및 프론트엔드 라우팅 라우터
    *   `organizer_pipeline.py`: 업로드된 사진을 연월/지역 폴더로 분류 및 찌꺼기 처리하는 정리 봇
    *   `vector_indexer.py`: AI 모델들을 대량 가동하여 벡터 DB(Qdrant)에 지식을 삽입하는 인덱싱 봇
    *   `xmp_utils.py`: 파생 메타데이터 XMP 스니펫 관리자
    *   기타 `docker-compose.yml`, `requirements.txt`, `Dockerfile`, `.env` 등 글로벌 세팅 파일
*   `📁 DebugTool/`
    *   시스템 진단, DB 조회, Qdrant 체크, 타입 에러 테스트 등을 위해 1회성으로 사용되는 각종 `check_*.py`, `remote_*.py`, `test_*.py` 스크립트 전용 방.
*   `📁 Scripts/`
    *   정기적으로 수동 실행이 필요하거나 유용한 배치(Batch) 관리자 도구.
    *   예: `enroll_batch.py`(얼굴 추가 학습), `generate_thumbnails_batch.py`, `bump_version.py` 등
*   `📁 OneTimeFixes/`
    *   과거에 시스템 대규모 리팩토링이나 데이터 교정을 위해 사용했던 일회성 스크립트 모음.
    *   예: `compress_sequence.py`(구멍 난 파일 번호 당기기), `translate_folders.py`(영어 위치명 한글 번역기)

---

## 🛡️ 3. 개발 제 1원칙 및 형상 관리 룰 (The Golden Rules)

> **[규칙 1. 원본 무결성 유지]**
> 어떠한 로직 개편이 있더라도, 사용자의 **원본 사진 및 내부 EXIF 메타데이터는 1%도 훼손되거나 조작되어서는 안 됩니다.**
> 데이터 무결성이 최우선입니다. 기존 사진 포맷(.heic, .jpg)을 압축 손실을 감수해가며 강제 단일 변환하거나, 파일 내부 픽셀/메타 헥스를 고치는 짓은 엄격히 금지됩니다. 모든 검색과 재배치는 오직 '디렉토리 Rename'과 '안전하게 파생된 DB 공간' 혹은 '비파괴적 XMP, WebP 동반 생성' 영역 안에서만 놀아야 합니다. 

> **[규칙 2. 문서 자기 주도 업데이트 엄수 (Self-Healing Docs)]**
> 코드를 작성하는 AI 에이전트(혹은 개발자)는 각 기술이나 기능에 대해 **수정/추가 내용이 발생하면, 관련된 모든 Markdown 문서(Plan, Progress, Architecture, Specs 등)를 스스로 먼저 스캔하여 즉시 최신 내용으로 동기화(업데이트)** 해두어야 합니다. 문서를 과거의 유산으로 방치하지 마십시오.

> **[규칙 3. 100% 롤백 보장 기조 (Zero-Risk Commit)]**
> 어떠한 사소한 작업이라도 **종료되는 그 즉시 해당 변경사항을 Git으로 Commit하고 Push** 하십시오. 치명적인 오류가 발생했을 때 언제든지 단 몇 초 만에 이전 상태로 안전하게 롤백(Rollback) 할 수 있는 안정성 버퍼를 항시 확보해 두어야 합니다.

위 가이드를 완벽히 습득하셨다면, 이제 가장 우수한 개발 지능을 통해 GumaPhoto 프로젝트에 기여해 주세요!
