# YoutubeToDoc - Context Handoff

이 문서는 다른 디바이스(Surface 랩탑 등)에서 원활하게 작업을 이어가기 위해 현재까지의 유튜브 문서화(YoutubeToDoc) 프로젝트 아키텍처, 구현 상태 및 다음 작업 목표를 요약한 핸드오프 문서입니다.

## 🏗️ 1. 아키텍처 및 기술 스택
- **Backend**: Python (Flask 기반) - `Server.py`가 전체 오케스트레이션을 담당.
- **Frontend**: 바닐라 HTML/CSS/JS (`index.html`, `style.css`, `script.js`). 최근 썸네일과 진행 상태, 태그를 보여주는 태스크 그리드(Task Grid) UI로 모던하게 개편됨.
- **AI Models & Processing**:
  - **텍스트/요약/번역**: Google **Gemini API** (`gemini-3.1-flash-lite-preview` 사용 - 429 Rate Limit 문제 회피용)
  - **음성 인식(STT)**: **Faster-Whisper** (Turbo 모델, CPU 기반 `int8` 연산 적용). 원래 Gemini나 `youtube_transcript_api`를 쓰려 했으나 음성 파일 미지원 및 YouTube 블락(429)으로 인해 로컬 오프라인 STT로 완전히 변경.
- **Database**: 
  - 진행 상태 저장: `data/task_status.json`
  - 벡터 검색: Qdrant (Docker 묶음 배포)
- **Deployment**: `docker-compose.yml`을 통해 윈도우 `HomeServer` 상에서 백그라운드 구동 중.

## ✅ 2. 구현 완료된 상태 (최근 해결 이슈)
1. **API Rate Limit 방어 로직 강화**:
   - `tenacity` 라이브러리를 사용해 Gemini API 호출 실패 시 지수 백오프 기반 재시도 로직(`generate_content_with_retry`) 구현.
   - 요청 간 4.1초 딜레이를 강제하여 15 RPM(초당/분당 제한) 준수 추가.
2. **Frontend Task History 개선**:
   - `index.html`에서 `createTaskCard`를 수정하여 유튜브 썸네일을 직접 클릭해 영상을 재생할 수 있는 모던한 목록 UI 구축.
3. **오디오 STT(자막 생성) 파이프라인 완벽 교체**:
   - Gemini 3.1 모델이 Audio 파일을 받지 못하는 문제로 인해 텍스트 출력값이 공백(Null)이 되며 요약과 상세보기 생성까지 덩달아 실패하는 치명적 버그 수정.
   - `YoutubeAnalyzer`의 경험을 살려 로컬 전용 **faster-whisper**(`whisper-turbo`)를 `Server.py` 안에 통합 적용 완료.
   - Docker가 재시작될 때마다 Whisper AI 모델(1.5GB)을 재다운로드하는 것을 막기 위해 `docker-compose.yml`에 `huggingface-cache` 전용 볼륨 마운트 처리.
4. **의존성(Dependency) 및 인코딩 수정**: 
   - 윈도우에서 `requirements.txt`에 Null 바이트(`\x00`)가 들어온 문제 말끔하게 정리.
5. **Nginx 관련 404 이미지 에러 패치**:
   - `/view/<task_id>/detail` 진입 시 상세보기 HTML에 들어가는 프레임 이미지 `src`가 Nginx 루트인 포트 8081 도메인으로 들어가 404를 내뱉던 버그를 찾아냄.
   - `url_for` 절대경로 대신 `../../output/<safe-title>/images/` 형태의 상대경로로 치환하도록 우회하여 수정한 상태.

> **⚠️ 향후 개발 원칙 합의 사항 (Surface 랩탑)**
> - 코드는 "오직 GitHub 서버"에만 푸시(Commit). 직접 홈서버(HomeServer)의 로컬 코드를 실시간으로 만지지 않는다.
> - 기능 개발 시: `로컬Surface 수정 -> GitHub 푸시 -> 홈서버 SSH접속 후 git pull -> 컨테이너 재가동` 순서의 배포 파이프라인으로 일관성을 유지하기로 약속됨.
> - **커밋 메시지 작성 규칙**: 어떤 기기에서 어떤 작업을 했는지 명확히 하기 위해 `(기기명) 간단한 작업 내용 요약` 형식으로 작성. (예: `(SurfacePro) Nginx 404 이미지 라우팅 경로 수정`) 날짜는 생략.

## 🚀 3. 다음으로 진행해야 할 작업 (Next Steps)
1. **STT 성능 및 속도 실무 테스트**:
   - 현재 `HomeServer` Docker 배포 환경에서 Faster Whisper CPU(int8) 모드가 영상의 길이에 맞춰 어느 정도의 성능/시간으로 자막을 추출해 내는지 관찰.
   - 속도 저하가 심할 경우, 병렬 Worker 수 또는 Beam Size를 조정할 필요가 있음.
2. **Confluence 위키 자동 발행 테스트**:
   - 자막과 요약(Summary) HTML이 이제 정상적으로 뽑히게 되었으므로, "완료(completed)된 태스크가 설정한 Confluence 페이지 경로로 무사히 Publish 되는지" 점검.
3. **Qdrant 경고 수정 (선택사항)**:
   - 로그의 `UserWarning: Api key is used with an insecure connection.`을 없애기 위해 gRPC 또는 보안 접속 구조 확인.
4. **Surface 랩탑 원격 개발 환경 체크**:
   - 지금 이 PR 내용 풀링(Pull) 후 로컬에서 돌려볼 때, Docker 기반이 아닌 Surface 랩탑 네이티브 Python 환경이라면 `faster-whisper` 동작을 위해 Visual Studio Build Tools 및 관련 설정이 추가로 필요할 수 있음.
