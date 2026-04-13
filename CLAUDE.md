# TheGumaLab — Claude 작업 가이드라인 (CLAUDE.md)

`TheGumaLab` (Guma LAB Universe) 내 모든 하위 프로젝트에 공통 적용되는 개발·동기화·배포 원칙 및 Claude Code 작업 지침. 3대 PC(**HomeServer / Gram / SurfacePro**) 간 협업과 무중단 홈서버 운영을 위해 엄격히 준수.

---

## 📦 0. 프로젝트 개요

HomeServer 중심의 **개인용 self-hosted 서비스 생태계**. 모든 서비스는 Docker Compose로 통합 관리되며 단일 Monorepo 구조.

**하위 프로젝트**: `GumaPhoto`(gumaphoto.guma3d.com) · `GumaStockReport` · `GumaImageAnalyzer` · `GumaServerStatus` · `GumaTube`(YoutubeToDoc 포함) · `Index`(WebAuthn 인증) · `Nginx`(리버스 프록시)

**도메인 컨벤션**: 모든 서비스는 `*.guma3d.com` 서브도메인 사용. 신규 서비스도 동일 규칙 적용.

---

## 🏗️ 1. 기본 개발 워크플로우

```
[Gram / SurfacePro] ──push──▶ [GitHub main] ──▶ [GitHub Actions] ──SSH──▶ [HomeServer]
                                                                                  │
                                                                    pull_update.bat (변경된 프로젝트만)
                                                                                  │
                                                                    watchfiles 감지 → Flask 프로세스 자동 재시작
```

코드 수정은 라이브 서버에 직접 하지 않고 **GitHub 경유**. feature branch 없이 `main` 직접 푸시를 기본으로 함 (개인 프로젝트). HomeServer에서의 핫픽스는 예외이며, 사후에 반드시 로컬에 역반영.

### 🤖 Claude 행동 지침 — 환경 판별 필수

작업 시작 전 `hostname` 또는 `$env:COMPUTERNAME`으로 **현재 PC를 먼저 확인**하고 아래 분기 실행:

**시나리오 A — HomeServer에서 직접 작업 중 (hostname: `Guma3D`)**
코드가 이미 HomeServer에 있으므로 **ssh/pull 단계 생략**.
1. 수정 → `git add` → commit (prefix: `HomeServerMain`)
2. `git pull --rebase` → `git push origin main`
3. push 시 GitHub Actions가 자동 배포 처리 (watchfiles가 재시작까지 담당)

**시나리오 B — Gram / SurfacePro에서 원격 작업 중**
1. 수정 → `git add` → commit (prefix: `Gram` 또는 `SurfacePro`)
2. `git pull --rebase` → `git push origin main`
3. **이후 자동**: GitHub Actions → SSH → pull_update.bat → watchfiles 재시작

**공통 원칙**
- `git push`만 하면 배포까지 자동 완료. 별도 SSH 배포 불필요.
- 파괴적/비가역 작업(force push, reset --hard, 컨테이너·볼륨 삭제, DB 마이그레이션 등)은 **반드시 사용자 확인** 후 진행.
- 배포 파이프라인 실패 시 임의로 우회/재시도하지 말고 **사용자에게 즉시 보고**.
- 로컬 sync 편의 스크립트: `sync_github.ps1` — hostname 자동 감지로 3대 PC 모두에서 그대로 사용 가능 (`Guma3D`→HomeServerMain, `guma3d-n`→Gram, 그 외→SurfacePro).

---

## 💬 2. 커밋 메시지 컨벤션

**형식**: `({PC_이름}) {type}: {변경 내용}`

- **PC_이름**: `SurfacePro` / `Gram` / `HomeServerMain` (정확히 이 표기)
- **type**: `feat` · `fix` · `hotfix` · `chore` · `refactor` · `docs`

**예시**
```
(SurfacePro) feat: add multi-device sync documentation
(Gram) fix: resolve api rate limit issue in server.py
(HomeServerMain) hotfix: update docker-compose.yml for new port
```

**원칙**
- 한 커밋 = 하나의 논리적 변경. 메시지는 *무엇*보다 ***왜***를 우선.
- AI는 `Co-Authored-By`나 광고성 푸터를 **자동으로 붙이지 않음** (개인 프로젝트).

---

## 🔑 3. 환경변수(.env) 및 민감 정보

- `.env`, `*.key`, `*credentials*.json` 등은 **절대 git 커밋 금지**. 각 하위 프로젝트 `.gitignore`에 등재 필수.
- 변경 시 반드시 **SCP / SFTP / SSH로 직접 덮어쓰기**:
  ```bash
  scp ./GumaPhoto/.env HomeServer:/d/TheGumaLab/GumaPhoto/.env
  ```
- GitHub 경유 동기화 **절대 금지**. 실수로 커밋된 민감 정보는 즉시 rotate 후 사용자에게 보고.

---

## 🐳 4. Docker & 배포

- 모든 서비스는 `docker-compose.yml`로 정의. 통합 compose 또는 하위 프로젝트별 compose 사용.
- 컨테이너 이름은 `{service}_{role}` 형식 (예: `gumaphoto_celery`, `gumaphoto_web`).
- 신규 서비스 추가 시 `Nginx/` 하위 리버스 프록시 설정도 함께 갱신.
- 범용 배포 스크립트 사용:
  ```bat
  pull_update.bat <ProjectName> [container_to_restart]
  REM 예: pull_update.bat GumaPhoto gumaphoto_celery
  REM     pull_update.bat GumaStockReport
  ```
- 대부분의 서비스는 소스코드를 bind mount(`.:/app`)로 사용. `pull_update.bat` 후 `docker compose up -d`는 실행 중인 컨테이너를 재시작하지 않음.
- **watchfiles 적용 서비스** (현재: `GumaStockReport`): `.py` 파일 변경 시 컨테이너 내부의 Flask 프로세스만 자동 재시작. 컨테이너 자체는 계속 실행 유지 → 다운타임 없음.
- **watchfiles 미적용 서비스**: pull_update.bat 후 수동으로 컨테이너 재시작 필요:
  ```bash
  ssh HomeServer "docker restart <container_name>"
  ```
- 신규 서비스에 watchfiles 적용 시: `requirements.txt`에 `watchfiles` 추가, Dockerfile CMD 변경 후 `docker compose up --build -d` 1회 실행.

---

## 🚀 5. GitHub Actions 자동 배포 (CI/CD)

**워크플로우 파일**: `.github/workflows/deploy.yml`

`main` 브랜치에 push하면 자동으로 실행:
1. 변경된 파일 목록 분석 → 영향받는 프로젝트만 선별
2. HomeServer에 SSH 접속
3. 해당 프로젝트의 `pull_update.bat` 실행 (git pull + docker compose up)
4. watchfiles가 `.py` 변경을 감지해 Flask 프로세스 자동 재시작

**선택적 배포 규칙** — 변경된 폴더의 프로젝트만 배포:
- `GumaStockReport/` 파일 변경 → `gumastockreport_app` 만 재시작
- `GumaPhoto/` 파일 변경 → `gumaphoto_web` 만 재시작
- 루트 파일만 변경 (`CLAUDE.md` 등) → 배포 없음

**재시작의 의미**: watchfiles는 **컨테이너 재시작이 아닌 컨테이너 내부 Python 프로세스 재시작**. 컨테이너는 살아있고 Flask만 재기동 → 다운타임 없음.

**GitHub Secret 설정** (일회성):
- `HOMESERVER_SSH_KEY`: `~/.ssh/id_ed25519_HomeServer` 개인키 내용
- GitHub → repo Settings → Secrets and variables → Actions에서 등록

**주의**: Dockerfile 변경(새 패키지 추가 등)은 이미지 재빌드가 필요하므로 자동 배포 후 수동으로 1회 실행 필요:
```bash
ssh HomeServer "cd /d D:\TheGumaLab\<Project> && docker compose up --build -d"
```

---

## 🔌 6. HomeServer SSH 원격 작업

**SSH 설정** (`~/.ssh/config`):
```
Host HomeServer
    HostName 219.254.245.175
    User guma3
    IdentityFile ~/.ssh/id_ed25519_HomeServer
```

**중요 — HomeServer는 Windows (cmd.exe)**. SSH 접속 시 셸이 cmd.exe이므로 경로 표기에 주의:
- ❌ 틀린 방식 (Git Bash 경로): `cd /d/TheGumaLab/GumaStockReport`
- ✅ 올바른 방식 (Windows cmd): `cd /d D:\TheGumaLab\GumaStockReport`

**자주 쓰는 SSH 명령 패턴**:
```bash
# git 상태 확인
ssh HomeServer "cd /d D:\TheGumaLab\<Project> && git log --oneline -5"

# 배포
ssh HomeServer "D:\TheGumaLab\pull_update.bat <ProjectName>"

# 컨테이너 재시작 (코드 변경 반영)
ssh HomeServer "docker restart <container_name>"

# 컨테이너 로그 확인
ssh HomeServer "docker logs <container_name> --tail 20"
```

`pull_update.bat`은 내부에서 `cd /d` 처리를 하므로 경로 없이 바로 실행 가능.

---

## 🗂️ 7. 리포지토리 구조

- **Monorepo**: 모든 하위 서비스는 `D:\TheGumaLab\` 아래 각자 루트 폴더로 존재.
- 각 하위 프로젝트는 자체 `README.md`, `docker-compose.yml`, `.env.example` 보유 가능.
- 공통 스크립트는 루트에 배치 (`pull_update.bat`, `sync_github.ps1`).
- 신규 프로젝트 폴더는 `Guma{기능}` 네이밍 규칙 준수.

---

## 📝 8. 문서화 원칙

- 각 하위 프로젝트는 최소 `README.md` 보유. 포함 내용: 서비스 목적/URL, 로컬 실행 방법, 필요 환경변수, 재배포 명령.
- 본 `CLAUDE.md`는 **글로벌 공통 규칙만** 담음. 프로젝트별 세부 사항은 해당 README로 분리.

---

*규칙 갱신이 필요하면 이 파일을 직접 수정하여 커밋.*
