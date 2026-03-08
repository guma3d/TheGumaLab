# YoutubeToDoc - Context Handoff

이 문서는 다른 디바이스(Surface 랩탑 등)에서 원활하게 작업을 이어가기 위해 현재까지의 유튜브 문서화(YoutubeToDoc) 프로젝트 아키텍처, 구현 상태 등을 요약한 핸드오프 문서입니다.

## 🏗️ 1. 아키텍처 및 기술 스택
- **Backend**: Python (Flask 기반) - `Server.py`가 전체 오케스트레이션을 담당.
- **Frontend**: 바닐라 HTML/CSS/JS (`index.html`, `style.css`, `script.js`). 최근 UI 개편으로 Completed Documents 아래 검색 모달 및 썸네일+태그 리스트 UI 적용 완료.
- **AI Models & Processing**:
  - **텍스트 요약/번역/태그 추출**: Google **Gemini API** (`gemini-3.1-flash-lite-preview` 사용)
  - **음성 인식(STT)**: **Faster-Whisper** (Turbo 모델, CPU 기반 `int8` 연산 적용). 로컬 오프라인 STT 파이프라인.
- **Database**: 
  - 진행 상태 저장: `data/task_status.json`
  - 벡터 검색: Qdrant (Docker 묶음 배포)
- **Deployment**: `docker-compose.yml`을 통해 윈도우 `HomeServer` 상에서 백그라운드 구동 중.

## ✅ 2. 구현 완료된 상태 (최근 해결 이슈)
1. **모던 Frontend 개선 및 검색 UI**:
   - `index.html` 기반의 프리미엄 UI 적용 (글래스모피즘 등).
   - "Completed Documents" 내 문서 검색 기능 추가 (팝업 형태의 모달 검색창 도입).
2. **AI 태그 추출 및 UI 렌더링**:
   - Gemini API를 활용한 영상 별 영문 핵심 태그 4개 자동 추출 기능.
   - 요약 문서(`summary.html`) 최상단 YouTube 썸네일 직하단에 에메랄드 그린 컬러(`var(--primary)`) 기반의 태그 바 표시. 과거 생성 문서도 `regen.py`로 전부 재생성.
3. **오디오 STT(자막 생성) 파이프라인 완벽 통합**:
   - 로컬 `faster-whisper`를 활용하여 Gemini Audio 지원 한계를 완벽히 극복함.
   - `docker-compose.yml` 상에 Whisper 캐시 마운트로 재다운로드 억제. 
4. **결과 렌더링 로직 통일 (`Server.py`)**:
   - HTML 생성 로직을 `Server.py` 내의 `generate_summary_html` 등 인라인 빌더로 교체.
   - 불필요하게 남아있던 `write_wiki.py`, `templates/index.html`, 테스트 배포 파일 및 마이그레이션 도구(ex. `cleanup_bad_docs.py`)들을 모두 삭제 및 걷어냄.
5. **API Rate Limit 방어 로직 강화**:
   - `tenacity` 기반 재시도 로직 및 분당 호출 수 딜레이 컨트롤 기능 탑재(4.1초).

> **⚠️ 개발 원칙 합의 사항 (Surface 랩탑)**
> - 코드는 "오직 GitHub 서버"에만 푸시(Commit). 직접 홈서버(HomeServer)의 로컬 코드를 실시간으로 만지지 않는다.
> - 기능 개발 시: `로컬Surface 수정 -> GitHub 푸시 -> 홈서버 SSH접속 후 git pull -> 컨테이너 재가동` 순서의 배포 파이프라인 유지.
> - **커밋 메시지 작성 규칙**: `(SurfacePro) 기능 수정 내용` (영어로 작성)
> - **🔑 환경변수(.env) 동기화 특별 규칙**: `.env` 파일(비밀번호, API 키 포함) 등은 `git status` 대상에서 배제됨. 따라서 `.env` 수정 시엔 **반드시 `scp 로컬경로 원격지경로` 방식이나 SSH 접속으로 서버에 덮어쓰기 동기화**할 것.
