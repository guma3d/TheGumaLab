# Index — CLAUDE.md

TheGumaLab 통합 랜딩 페이지 및 WebAuthn 인증 서비스.

**로컬 포트**: 8081

---

## 기술 스택
- **Backend**: Python / FastAPI
- **인증**: WebAuthn (FIDO2 패스키 기반, 비밀번호 없음)

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `Index_Page` | 웹 서버 (포트 8081) |

## 환경변수
`.env`는 서비스 내부(`Index/.env`) 사용. GitHub 커밋 금지.

## 중요 데이터 파일
- `webauthn_credentials.json` — 등록된 패스키 자격증명 저장소. **절대 git 커밋 금지**, 손실 시 재등록 필요.

## 배포
```bat
pull_update.bat Index
```

## 주의사항
- `webauthn_credentials.json` 변경 시 반드시 SCP로 별도 백업.
- 이 서비스가 다운되면 모든 서비스의 인증 관문이 막힐 수 있음.
