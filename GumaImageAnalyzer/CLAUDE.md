# GumaImageAnalyzer — CLAUDE.md

이미지 분석 유틸리티 서비스.

**로컬 포트**: 5000

> **전역 규칙 참조**
> - 환경변수 / API 키: 루트 `D:\TheGumaLab\.env` 사용
> - 워크플로우·커밋·배포 규칙: 루트 `CLAUDE.md` 준수

---

## 기술 스택
- **Backend**: Python / Flask
- **분석**: `analyze.py` 기반 이미지 처리

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `gumaimageanalyzer_app` | Flask 웹 서버 (포트 5000) |

## 볼륨
- `./uploads` → 업로드된 분석 대상 이미지

## 배포
```bat
pull_update.bat GumaImageAnalyzer
```

## 주의사항
- `uploads/` 폴더는 git 제외 대상.
- GumaPhoto와 역할 중복 여부 주기적으로 검토 필요.
