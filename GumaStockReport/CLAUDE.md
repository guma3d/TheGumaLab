# GumaStockReport — CLAUDE.md

개인 주식 리포트 PWA. 관심 종목 모니터링·분석 대시보드.

**로컬 포트**: 8050

---

## 기술 스택
- **Backend**: Python (Dash / Flask 계열)
- **Cache**: Redis
- **Frontend**: PWA (manifest + service worker)
- **DB**: SQLite (`watchlist.db`)

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `gumastockreport_app` | 웹 앱 서버 (포트 8050) |
| `gumastockreport_redis` | 캐시 (포트 6380) |

## 환경변수
`.env`는 서비스 내부(`GumaStockReport/.env`) 사용. GitHub 커밋 금지.

## 배포
```bat
pull_update.bat GumaStockReport
```

## 주의사항
- `watchlist.db` SQLite 파일은 git 추적 여부 확인 필요. 데이터 파일이므로 제외 권장.
