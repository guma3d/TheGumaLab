# YoutubeToDoc 구현 로드맵 및 상태
이 문서는 기존 `movie2imgs` 프로젝트의 핵심 기능(AI 스크립트화, 번역, 이미지 분류 등)을 새로운 프리미엄 UI인 `YoutubeToDoc` 서비스에 매끄럽게 이식하기 위한 작업 계획이었으며, 현재는 **모든 주요 이식 및 고도화가 완료된 상태**입니다.

## 🎯 주요 목표 (달성 완료)
기존의 강력한 백엔드 분석 로직(Gemini, 큐 시스템, 벡터 검색엔진)을 고급스러운 Glassmorphism UI 프론트엔드(`YoutubeToDoc`)에 통합하여 일체감 있는 서비스를 성공적으로 구축했습니다.

---

## 📅 단계별 구현 및 완료 내역

### 1단계: 인프라 및 의존성 세팅 (Docker 환경 구축) - 완료
- [x] `Dockerfile` 변경: OS 레벨 종속성(`ffmpeg`, `opencv` 구동을 위한 패키지) 추가
- [x] `docker-compose.yml` 갱신: Qdrant(구문 검색 벡터DB) 컨테이너 및 Gemini 연결, Whisper STT 모델 로컬 캐시 마운트 적용
- [x] `requirements.txt` 병합: Flask, OpenCV, Google GenAI, Qdrant 등 필수 엔진 세팅 완료

### 2단계: 백엔드 엔진 이식 (`Server.py`) - 완료
- [x] 큐(Queue) 상태 추적 로직 및 백그라운드 워커 스레드 완전 이식
- [x] 비디오 다운로드, 오디오 추출 로직 통합
- [x] 로컬 전용 **faster-whisper (turbo)** 자막 생성(STT) 파이프라인 탑재
- [x] Gemini 프롬프트 로직 및 번역/영문 태그(4개) 자동 추출 로직 병합 완료
- [x] Qdrant 기반 벡터화 및 시맨틱 검색 엔진 적용

### 3단계: 프론트엔드 연동 (`script.js` & `index.html`) - 완료
- [x] 기존 거친 렌더링 방식을 벗어나, `index.html` 기반의 최신 로딩/폴링/퍼센티지 매핑 적용 (10단계 상태 진행률)
- [x] "Completed Documents" 내 문서 검색 모달 팝업 최신 기능 및 Thumbnail 기반 갤러리 뷰 연동

### 4단계: 렌더링 템플릿 파일 복사 및 적용 - 완료
- [x] 이전 `templates/` 하위 HTML 파일들을 활용하는 구조를 걷어내고, `Server.py` 상에서 다이나믹하게 인라인 HTML 렌더링을 하도록 개선 (`generate_summary_html` 등).
- [x] 요약 문서 UI 최적화 완료 (그린 테마 적용, 삭제 버튼 CSS 정리, 영상 썸네일과 하단 추출 태그 렌더링 연동).
- [x] 불필요한 레거시 코드(`write_wiki.py`, 마이그레이션 도우미 스크립트 등) 전부 클린 제거.

### 5단계: 최종 테스트 및 배포 (홈서버 동기화) - 완료
- [x] 깃허브(GitHub) 동기화 (기존 확립된 `/sync_github` 파워셸 스크립트 이용) 성공적 운용.
- [x] 타겟 홈서버(HomeServer) 도커 컨테이너 빌드 및 최종 가동 성능 점검 완료. 재생성(`regen.py`) 스크립트 동작 확인.

---
*참고: 초기에는 `movie2imgs_extracted` 원본 코드를 기반으로 시작했으나, 현재는 완전히 `YoutubeToDoc` 전용 코드 규격으로 독립/정제 완료되었습니다.*
