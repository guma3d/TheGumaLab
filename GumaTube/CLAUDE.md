# GumaTube — CLAUDE.md

YouTube 영상 다운로드·자막 추출·문서화 도구 (YoutubeToDoc 포함).

**로컬 포트**: 8083

---

## 기술 스택
- **Backend**: Python / Flask
- **영상 처리**: yt-dlp (다운로드), HuggingFace (STT/임베딩)
- **Vector DB**: Qdrant
- **GPU**: NVIDIA GPU 사용 (STT·임베딩 추론)

## 컨테이너 구성
| 컨테이너 | 역할 |
|---|---|
| `gumatube_app` | Flask 웹 서버 (포트 8083) |
| `gumatube_qdrant` | 벡터 검색 DB (포트 6334) |

## 볼륨 (데이터 경로)
- `./data` → 다운로드된 영상/오디오 원본
- `./output` → 생성된 문서 결과물
- `./yt-dlp-cache` → yt-dlp 캐시
- `./huggingface-cache` → HuggingFace 모델 캐시 (용량 클 수 있음)

## 환경변수
`.env`는 서비스 내부(`GumaTube/.env`) 사용. GitHub 커밋 금지.

## 배포
```bat
pull_update.bat GumaTube
```

## 주의사항
- `huggingface-cache`는 모델 파일로 수백MB~수GB 될 수 있음. git에 절대 포함 금지.
- `data/`, `output/`도 git 제외 대상.
