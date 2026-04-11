# Nginx — CLAUDE.md

리버스 프록시 및 Cloudflare Tunnel 허브. 모든 `*.guma3d.com` 트래픽의 진입점.

> **전역 규칙 참조**
> - 환경변수 / API 키: 루트 `D:\TheGumaLab\.env` 사용
> - 워크플로우·커밋·배포 규칙: 루트 `CLAUDE.md` 준수

---

## 구성
- **Nginx**: 도메인별 라우팅 (`nginx.conf`)
- **Cloudflared**: Cloudflare Tunnel로 외부 인터넷 ↔ HomeServer 연결 (포트 포워딩 불필요)

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `HomeServer_Nginx` | 리버스 프록시 (포트 80) |
| `HomeServer_Cloudflared` | Cloudflare Tunnel 클라이언트 |

## 새 서비스 추가 시
`nginx.conf`에 서브도메인 → 내부 포트 라우팅 추가 후 재시작:
```bat
pull_update.bat Nginx
```

## 주의사항
- **Nginx 설정 오류 = 전체 서비스 접근 불가**. 수정 전 `nginx -t`로 문법 검증 필수.
- Cloudflare Tunnel 토큰은 `docker-compose.yml`에 하드코딩 되어있음 → git 공개 레포 전환 시 반드시 제거하고 `.env`로 분리.
- 이 서비스를 재시작할 때는 다운타임이 생기므로 사용자에게 먼저 확인.
