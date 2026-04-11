# GumaServerStatus — CLAUDE.md

HomeServer 상태 모니터링 대시보드.

**로컬 포트**: 8080

> **전역 규칙 참조**
> - 환경변수 / API 키: 루트 `D:\TheGumaLab\.env` 사용
> - 워크플로우·커밋·배포 규칙: 루트 `CLAUDE.md` 준수

---

## 기술 스택
- **Backend**: Python (Flask / 단순 스크립트)
- **특이사항**: 호스트의 C드라이브·D드라이브를 읽기 전용 마운트해 디스크 사용량 등 시스템 정보 수집

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `gumaserverstatus_app` | 모니터링 웹 서버 (포트 8080) |

## 볼륨
- `C:\` → `/mnt/c` (읽기 전용)
- `D:\` → `/mnt/d` (읽기 전용)

## 배포
```bat
pull_update.bat GumaServerStatus
```

## 주의사항
- 호스트 파일시스템을 마운트하므로 **HomeServer 전용**. 다른 PC에서는 정상 동작 안 함.
- `extra_hosts: host.docker.internal` 설정으로 호스트 네트워크 접근 중.
