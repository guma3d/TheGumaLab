# TheGumaLab 글로벌 개발 및 동기화 가이드라인 (Global Development Guidelines)

이 문서는 `TheGumaLab` 내의 모든 하위 프로젝트 및 서비스에 공통으로 적용되는 개발, 동기화, 배포 원칙입니다. 3대의 PC(HomeServer, Gram, SurfacePro) 간의 원활한 협업과 무중단 서비스 운영을 위해 아래 규칙을 엄격히 준수합니다.

## 🏗️ 1. 기본 개발 워크플로우
모든 프로젝트의 코드 수정은 직접 라이브 서버(HomeServer)에서 진행하지 않고, 로컬 디바이스에서 작업 후 GitHub을 경유하여 배포하는 파이프라인을 따릅니다.

1. **로컬 작업**: `Gram`, `SurfacePro` 등의 로컬 PC에서 코드 작성 및 테스트.
2. **버전 관리**: 변경 사항을 GitHub 서버로 Push (Commit).
3. **서버 반영**: HomeServer(메인 컴퓨터)에서 SSH 접속 또는 자동화 스크립트를 통해 `git pull` 수행.
4. **서비스 재가동**: 필요 시 Docker 컨테이너 재시작 등 배포 파이프라인 가동.

⚠️ **개발 원칙 합의 사항**
- 코드는 **오직 GitHub 서버**에만 푸시(Commit)합니다.
- 홈서버(HomeServer)의 구동 중인 로컬 코드를 실시간으로 직접 수정하지 않습니다. (핫픽스 제외)

## 💬 2. 커밋 메시지 작성 규칙 (Commit Convention)
어떤 디바이스에서 작업이 이루어졌는지 명확히 추적하기 위해 커밋 메시지 최상단에 물리적 PC 이름을 명시해야 합니다.

- **규칙**: `({PC_이름}) {기능 수정 내용}` (영어 또는 한글로 명확히 작성)
- **예시**:
  - `(SurfacePro) feat: add multi-device sync documentation`
  - `(Gram) fix: resolve api rate limit issue in server.py`
  - `(HomeServer) hotfix: update docker-compose.yml for new port`

## 🔑 3. 환경변수(.env) 및 민감한 정보 동기화 규칙
API 키, 데이터베이스 패스워드 등이 포함된 `.env` 파일은 보안상 `git status` 추적 대상에서 철저히 배제됩니다. (`.gitignore`에 추가 필수)

- **.env 수정 및 동기화 방법**:
  - `.env` 파일에 변경이 생길 경우, **반드시 `scp 로컬경로 원격지경로` 방식이나 SSH/SFTP 접속**을 이용하여 해당 서버에 직접 덮어쓰기 형태로 동기화해야 합니다.
  - GitHub을 통한 동기화는 절대 금지됩니다.

---
*해당 가이드라인은 YoutubeToDoc을 포함한 TheGumaLab의 모든 신규/기존 서비스 개발 시 기본 개념으로 적용됩니다.*
