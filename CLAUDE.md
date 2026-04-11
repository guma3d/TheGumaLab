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
[Gram / SurfacePro] ──push──▶ [GitHub main] ──pull──▶ [HomeServer] ──▶ [Docker restart]
```

코드 수정은 라이브 서버에 직접 하지 않고 **GitHub 경유**. feature branch 없이 `main` 직접 푸시를 기본으로 함 (개인 프로젝트). HomeServer에서의 핫픽스는 예외이며, 사후에 반드시 로컬에 역반영.

### 🤖 Claude 행동 지침 — 환경 판별 필수

작업 시작 전 `hostname` 또는 `$env:COMPUTERNAME`으로 **현재 PC를 먼저 확인**하고 아래 분기 실행:

**시나리오 A — HomeServer에서 직접 작업 중 (hostname: `Guma3D`)**
코드가 이미 HomeServer에 있으므로 **ssh/pull 단계 생략**.
1. 수정 → `git add` → commit (prefix: `HomeServerMain`)
2. `git pull --rebase` → `git push origin main`
3. 필요 시 `docker compose up -d` / 해당 워커 `docker restart`

**시나리오 B — Gram / SurfacePro에서 원격 작업 중**
1. 수정 → `git add` → commit (prefix: `Gram` 또는 `SurfacePro`)
2. `git pull --rebase` → `git push origin main`
3. `ssh HomeServer` → 해당 프로젝트의 `pull_update.bat` 실행
4. 관련 Docker 워커 재시작 확인

**공통 원칙**
- 수정 완료 시 별도 지시가 없어도 위 절차를 자동 One-Stop 수행.
- 파괴적/비가역 작업(force push, reset --hard, 컨테이너·볼륨 삭제, DB 마이그레이션 등)은 **반드시 사용자 확인** 후 진행.
- 배포 파이프라인 실패 시 임의로 우회/재시도하지 말고 **사용자에게 즉시 보고**.
- 로컬 sync 편의 스크립트: `sync_github.ps1` (내부 PC prefix는 호스트에 맞게 교체).

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
- 배포 스크립트는 루트 `pull_update.bat` 패턴을 따름:
  ```bat
  cd /d D:\TheGumaLab\{project}
  git fetch origin main
  git reset --hard origin/main
  docker compose up -d
  docker restart {critical_worker}
  ```

---

## 🗂️ 5. 리포지토리 구조

- **Monorepo**: 모든 하위 서비스는 `D:\TheGumaLab\` 아래 각자 루트 폴더로 존재.
- 각 하위 프로젝트는 자체 `README.md`, `docker-compose.yml`, `.env.example` 보유 가능.
- 공통 스크립트는 루트에 배치 (`pull_update.bat`, `sync_github.ps1`, `setup_git_hooks.bat`).
- 신규 프로젝트 폴더는 `Guma{기능}` 네이밍 규칙 준수.

---

## 📝 6. 문서화 원칙

- 각 하위 프로젝트는 최소 `README.md` 보유. 포함 내용: 서비스 목적/URL, 로컬 실행 방법, 필요 환경변수, 재배포 명령.
- 본 `CLAUDE.md`는 **글로벌 공통 규칙만** 담음. 프로젝트별 세부 사항은 해당 README로 분리.

---

*규칙 갱신이 필요하면 이 파일을 직접 수정하여 커밋.*
