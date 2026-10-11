# GumaTTS — 공통 음성 작업실

모든 신규 영상 음성의 생성·원본 보관·한국어 청취 비교를 한곳에서 관리한다.

- 웹: https://home.guma3d.com/gumatts/ (HomeServer SSO)
- 로컬: `D:\TheGumaLab\GumaTTS`, 컨테이너 `GumaTTS_app`, 포트 8088
- Story: Qwen3-TTS 1.7B CustomVoice / Sohee 시험. 0.6B와 동일 원고 비교. 자연스러운 한국어와 장시간 청취 품질을 우선하며 사용자 청취 전 기본 음성으로 확정하지 않는다.
- Food·Tech·Living: 기존 Zephyr 유지, 생성 요청은 이 서비스로 통합. 기존 음성·영상 보존.
- 로컬은 API 요금·호출 한도 없음. 전력·GPU·생성 시간은 필요하다. Gemini는 프로젝트 결제 등급에 따라 과금 가능. 실패 시 유료 API 자동 대체 없음.

## 구조와 보존

VideoFactory / Story → 공통 `client.py` → 인증된 작업 API → SQLite FIFO → 단일 생성 프로세스 → 원본 WAV + 정규화 MP3 + 생성 기록 → 웹 청취 검수.

한 번에 한 작업만 GPU를 사용하며 작업 프로세스 종료 시 VRAM을 해제한다. CPU 스레드 4개, BF16, SDPA 사용. 장문은 문단별로 생성하고 Story의 기존 문단 재사용을 유지한다. 동일 원고·모델·스타일·시드·프로젝트·제목은 대기/진행/완료 중복 생성을 막는다. 실패본을 보존하고 새 요청으로 재시도한다. 재시작 당시 진행 중이던 작업은 실패로 기록하며 자동으로 다시 과금하지 않는다.

`storage/jobs.sqlite3`, `storage/<job-id>/{request.json,original.wav,audio.mp3,result.json,worker.log}`에 저장한다. 모델 캐시는 `models/`. 원본·모델·DB·토큰은 Git 제외. GPU 최대치는 PyTorch allocated peak로 전체 프로세스 VRAM과 다를 수 있다. 초기 다운로드/로딩 시간과 생성 시간을 구분한다. 기술적 디코드 성공은 발음·누락·자연스러움 통과가 아니다.

## 실행·배포

```powershell
cd D:\TheGumaLab\GumaTTS
docker compose up -d --build
docker exec GumaTTS_app python -m pytest tests -q
docker exec HomeServer_Nginx nginx -t
docker exec HomeServer_Nginx nginx -s reload
```

NVIDIA GPU 지원 Docker Desktop/WSL2 필요. 첫 요청 때 공식 Hugging Face 저장소에서 모델을 내려받아 캐시하며 HF 토큰은 필요 없다. 시작 시 생성되는 `storage/service-token`을 VideoFactory에 읽기 전용 마운트한다. 새 호스트에서는 GumaTTS를 먼저 시작한다. GitHub Actions 배포 대상에 포함한다.

환경변수: `GUMATTS_AUTH_URL` (Index `/auth`), `GUMATTS_STORAGE` (storage), `HF_HOME` (/models), `GEMINI_API_KEY` (기존 외부 음성 유지 시만 필요, 서버 .env). 클라이언트: `GUMATTS_URL`, `GUMATTS_TOKEN_FILE`, `GUMATTS_CLIENT_PATH`. 비밀값을 URL·화면·로그에 출력하지 않는다. 브라우저는 SSO+동일 출처 쓰기 헤더, 제작기는 파일 기반 Bearer 토큰을 사용한다.

## API

- `POST /api/jobs`: text, model(qwen-1.7b/qwen-0.6b/gemini-flash/gemini-lite), voice, style, project, title. 외부 모델에는 allow_cloud=true 필요.
- `GET /api/jobs/<id>`: 상태와 생성 기록.
- `GET /media/<id>/mp3|wav|manifest`: 인증된 다운로드.
- `POST /api/jobs/<id>/review`: pending/approved/changes + note. 해당 음성만 평가하며 채널 기본 목소리나 YouTube 승인을 변경하지 않는다.

클라이언트는 SHA256을 확인하고 `.tts.json`에 작업 ID와 실제 모델을 기록한다. 기존 파일과 해시가 다르면 덮어쓰지 않는다. 다른 모델·원고로 재개할 때는 새 버전 폴더를 사용한다.

## 품질 기준

[Qwen 공식 모델](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)은 Apache 2.0, 한국어 Sohee 지원. 1.7B는 말투 지시를 적용하고 0.6B는 적용하지 않는다. 동일 원고의 이야기체·질문·숫자·외래어를 비교하고 실제 청취로 발음, 억양, 누락, 반복, 호흡을 확인한다. 긴 영상 전환은 샘플 청취 결과를 먼저 반영한다. 생성·웹 저장 허가는 YouTube 업로드 허가가 아니다.
