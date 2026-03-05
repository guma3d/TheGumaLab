# YoutubeToDoc 구현 로드맵
이 문서는 기존 `movie2imgs` 프로젝트의 핵심 기능(AI 스크립트화, 번역, 이미지 분류 등)을 새로운 프리미엄 UI인 `YoutubeToDoc` 서비스에 매끄럽게 이식하기 위한 작업 계획입니다. 개발 과정 동안 이 로드맵을 지침으로 삼습니다.

## 🎯 주요 목표
기존의 강력한 백엔드 분석 로직(Gemini, 큐 시스템, 벡터 검색엔진)을 방금 작성한 고급스러운 Glassmorphism UI 프론트엔드(`YoutubeToDoc`)에 통합하여 일체감 있는 서비스를 제공합니다.

---

## 📅 단계별 구현 계획

### 1단계: 인프라 및 의존성 세팅 (Docker 환경 구축)
- [x] `Dockerfile` 변경: OS 레벨 종속성(`ffmpeg`, `opencv` 구동을 위한 패키지) 추가
- [x] `docker-compose.yml` 갱신: Qdrant(구문 검색 벡터DB) 컨테이너 및 Gemini 연결을 위한 환경 변수 세팅 추가
- [x] `requirements.txt` 병합: Flask, OpenCV, Google GenAI, Qdrant 등 기존 코드가 필요로 하는 라이브러리를 새 프로젝트 설치 목록에 통합

### 2단계: 백엔드 엔진 이식 (`Server.py`)
- [x] 큐 시스템(Queue) 및 상태 추적 로직 `youtube_processor.py`에서 `Server.py`로 가져오기
- [x] 비디오 다운로드, 오디오 추출, Whisper 자막 생성 관련 백그라운드 프로세싱 함수 복사 및 조정
- [x] 타임스탬프 기준 이미지 추출 및 중복 이미지 감지 처리 함수 추가
- [x] Gemini 번역 모델 통신 로직 병합
- [x] SQLite를 이용한 선호도 저장 및 Qdrant를 이용한 시맨틱 검색 로직 적용
- [x] 부가 스크립트 파일(`migrate_task_status_to_video_id.py`) 이식

### 3단계: 프론트엔드 연동 (`script.js` & `index.html`)
- [x] 기존 HTML의 거친 로딩/폴링(Polling) 방식을 제거하고, `script.js`의 프리미엄 로딩 애니메이션에 연동
- [x] 백엔드의 `TASK_STATUS`(`queued`, `downloading`, `transcribing`, `extracting_images`, `translating`, `generating_html`, `completed`) 데이터를 새 UI의 진행률 퍼센트(%) 및 상태 텍스트로 자연스럽게 매핑하여 화면에 출력
- [x] 결과물을 보여주는 컨테이너 렌더링 로직 연동

### 4단계: 렌더링 템플릿 파일 복사 및 적용
- [x] 분석 완료 시 생성되는 결과 리포트 HTML 디자인(기존 `templates/` 폴더 내 파일들) 복사
- [x] 결과 HTML 파일을 렌더링할 때 새 서비스 테마에 어울리도록 일부 CSS 연동 검토

### 5단계: 최종 테스트 및 배포 (홈서버 동기화)
- [x] `.env` 파일 등에 Gemini API Key 셋업 가이드 및 적용
- [ ] 깃허브(GitHub) 동기화 (기존 확립된 `/sync_github` 워크플로우 이용)
- [ ] 타겟 홈서버(HomeServer)에서 도커 컨테이너 빌드 및 최종 가동 테스트

---
*참고: 기존 원본 코드는 `C:\Users\guma3d\Downloads\movie2imgs_extracted\movie2imgs-main`에서 복사하여 재활용합니다.*
