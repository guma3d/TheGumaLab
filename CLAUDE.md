# TheGumaLab — Claude 작업 가이드라인 (CLAUDE.md)

`TheGumaLab` (Guma LAB Universe) 내 모든 하위 프로젝트에 공통 적용되는 개발·동기화·배포 원칙 및 Claude Code 작업 지침. 3대 PC(**HomeServer / Gram / SurfacePro**) 간 협업과 무중단 홈서버 운영을 위해 엄격히 준수.

---

## 📦 0. 프로젝트 개요

HomeServer 중심의 **개인용 self-hosted 서비스 생태계**. 모든 서비스는 Docker Compose로 통합 관리되며 단일 Monorepo 구조.


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
  ```
- GitHub 경유 동기화 **절대 금지**. 실수로 커밋된 민감 정보는 즉시 rotate 후 사용자에게 보고.

---

## 🐳 4. Docker & 배포

- 모든 서비스는 `docker-compose.yml`로 정의. 통합 compose 또는 하위 프로젝트별 compose 사용.
- 신규 서비스 추가 시 `Nginx/` 하위 리버스 프록시 설정도 함께 갱신.
- 범용 배포 스크립트 사용:
  ```bat
  pull_update.bat <ProjectName> [container_to_restart]
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

## 📱 6-1. 모바일 Claude Code — HomeServer 원격 제어

외출 중 모바일(claude.ai/code)에서 HomeServer를 조작하기 위한 경로. 웹 샌드박스는 직접 SSH 불가 → **GitHub Actions `workflow_dispatch`를 프록시**로 사용.

**워크플로우 파일**: `.github/workflows/server-control.yml`

**지원 action**:
- `status` — `docker ps` 전체 컨테이너 상태
- `logs` — `docker logs <container> --tail N` (입력: `container`, 선택 `log_lines`)
- `restart` — `docker restart <container>` (입력: `container`)
- `pull` — `pull_update.bat <project>` 실행 = git reset --hard origin/main + `docker compose up -d` (입력: `project`)
- `rebuild` — `docker compose up --build -d` (입력: `project`, Dockerfile 변경·신규 패키지 반영용)
- `compose-ps` — 프로젝트의 docker compose ps (입력: `project`)
- `disk` — `docker system df`

**실행 방법**
- 웹 UI: Actions → "HomeServer Control" → Run workflow → 입력 후 실행
- 모바일 Claude Code: MCP GitHub 툴로 workflow_dispatch 트리거 → 완료 후 Job Summary 조회

**결과 확인**: 모든 출력은 Job Summary에 마크다운 표 + 코드블록으로 기록 (tail 2000줄 제한).

**주의**
- 본 워크플로우는 `HOMESERVER_SSH_KEY` 시크릿에 의존. 키 유출 시 즉시 rotate.
- `concurrency` 그룹으로 동시 실행 방지 — 요청 중첩 시 순차 처리.
- 파괴적 작업(rebuild, pull — git reset --hard 포함)은 모바일에서도 신중히. 미커밋 홈서버 변경분은 `pull`/`rebuild` 시 소실됨.

---

## ✅ 6-2. Codex 검증된 HomeServer 배포 경로

로컬 PC에서 `ssh HomeServer` 별칭이나 `~/.ssh/id_ed25519_HomeServer` 키가 없으면 직접 SSH에 집착하지 말고 GitHub Actions `HomeServer Control` 워크플로우를 사용한다. 현재 이 경로가 실제로 성공한 표준 fallback이다.

**성공 절차**:
1. 로컬에서 수정·검증 후 커밋.
2. GitHub SSH push 전 PowerShell 세션에 `$env:GIT_SSH="C:\Windows\System32\OpenSSH\ssh.exe"` 설정.
3. `git push origin main`.
4. 홈서버 반영:
   ```bash
   gh workflow run server-control.yml --ref main -f action=pull -f project=<ProjectName>
   gh run watch <run_id> --exit-status
   ```
5. 컨테이너 재시작이 필요한 서비스는 별도 실행:
   ```bash
   gh workflow run server-control.yml --ref main -f action=restart -f container=<container_name>
   gh run watch <run_id> --exit-status
   ```
6. 최종 확인:
   ```bash
   gh workflow run server-control.yml --ref main -f action=logs -f container=<container_name> -f log_lines=40
   gh run watch <run_id> --exit-status
   ```

**GumaKidsPython 기준값**:
- project: `GumaKidsPython`
- container: `gumakidspython_app`
- 검증 성공 로그: `Container gumakidspython_app Started`, `gumakidspython_app Up`, `Serving Flask app 'server'`, `Running on http://127.0.0.1:5000`

**실패 대응**:
- `docker-credential-desktop` 오류는 `pull_update.bat`의 임시 `DOCKER_CONFIG` fallback으로 처리한다.
- `pull_update.bat` 자체를 갱신한 직후 첫 실행이 중간 실패하면, 홈서버 작업트리가 새 커밋으로 reset됐는지 로그에서 `HEAD is now at <commit>`을 확인하고 같은 `pull` 워크플로우를 한 번 더 실행한다.

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
