# GumaTTS — 공통 음성 작업실

- 2026-10-17 톤 최종 승인: Sohee + sohee-upbeat-v1 고정. 정확한 영문 말투 지시·seed=43·모델 revision·승인 샘플 작업/해시는 GumaTTS/voice-policy.json이 기준이다. 승인 샘플 51af3c5b9e9e491dbcca532dd3b75693의 문장 끝까지 밝고 신나는 톤을 유지한다. 차분한 기본 톤으로 되돌리거나 컷마다 다른 감정 지시를 넣지 않는다. 샘플 승인은 전체 재생성본의 청취·업로드 승인과 구분한다.
- 2026-10-17 사용자 확정: 앞으로 새로 생성하는 모든 내레이션은 한국어 기본 화자 Sohee, Qwen3-TTS 1.7B CustomVoice(qwen-1.7b), language=Korean으로 고정한다. F4 VoiceDesign/복제 및 Zephyr 등 다른 화자로 자동 대체하지 않는다. 쇼핑쇼츠는 전체 대사를 한 번에 생성하고 최종 음성은 분할 재접합 없는 연속 마스터로 사용한다. 피치·배속 변경 없이 발화 경계에 영상·자막을 맞춘다. 사용자가 승인한 밝고 신나는 sohee-upbeat-v1 말투(미소·가벼운 발성·끝음절까지 밝은 에너지)를 그대로 사용하고 모델·화자·한국어 설정·작업 ID·원본·마스터 해시를 보존한다. 모든 컷의 발음·무음·잘림·음량·BGM 대비·로고를 검사하되 실제 청취와 자동 검사를 구분한다. 기존 결과와 과거 승인은 보존하며 이번 샥즈 영상만 새 버전으로 교체한다. 음성 정책은 업로드·공개 승인이 아니다.
현재 제작 정책은 [통합 안내](../GumaDdanjit/docs/guide-index.md)를 먼저 읽는다. 날짜가 있는 과거 제작·검증 예시는 현재 완료나 승인 범위 보장이 아니다.

모든 신규 영상 음성의 생성·원본 보관·한국어 청취 비교를 한곳에서 관리한다.

- 웹: https://home.guma3d.com/gumatts/ (HomeServer SSO)
- 로컬: `D:\TheGumaLab\GumaTTS`, 컨테이너 `GumaTTS_app`, 포트 8088
- 로컬은 API 요금·호출 한도 없음. 전력·GPU·생성 시간은 필요하다. Gemini는 프로젝트 결제 등급에 따라 과금 가능. 실패 시 유료 API 자동 대체 없음.

## 구조와 보존

VideoFactory / Story → 공통 `client.py` → 인증된 작업 API → SQLite FIFO → 단일 생성 프로세스 → 원본 WAV + 정규화 MP3 + 생성 기록 → 웹 청취 검수.

한 번에 한 작업만 GPU를 사용하며 작업 프로세스 종료 시 VRAM을 해제한다. CPU 스레드 4개, BF16, SDPA 사용. 제작 음성의 생성 단위는 공간별 지침을 따른다. 쇼핑은 전체 대사 단일 생성·연속 마스터, Story는 Gemini Flash / Zephyr의 구간별 생성·정상 구간 재사용이다. 일반 비교 모델의 문단 생성 기능을 모든 제작의 기본값으로 확대하지 않는다. 동일 원고·모델·스타일·시드·프로젝트·제목은 대기/진행/완료 중복 생성을 막는다. 실패본을 보존하고 새 요청으로 재시도한다. 재시작 당시 진행 중이던 작업은 실패로 기록하며 자동으로 다시 과금하지 않는다.

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

- `POST /api/jobs`: text, model(qwen-design-1.7b/qwen-1.7b/qwen-0.6b/gemini-flash/gemini-lite), voice, style, project, title. 외부 모델에는 allow_cloud=true 필요.
- `GET /api/jobs/<id>`: 상태와 생성 기록.
- `GET /media/<id>/mp3|wav|manifest`: 인증된 다운로드.
- `POST /api/jobs/<id>/review`: pending/approved/changes + note. 해당 음성만 평가하며 채널 기본 목소리나 YouTube 승인을 변경하지 않는다.

클라이언트는 SHA256을 확인하고 `.tts.json`에 작업 ID와 실제 모델을 기록한다. 기존 파일과 해시가 다르면 덮어쓰지 않는다. 다른 모델·원고로 재개할 때는 새 버전 폴더를 사용한다.

## 품질 기준

[Qwen 공식 모델](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)은 Apache 2.0, 한국어 Sohee 지원. 1.7B는 말투 지시를 적용하고 0.6B는 적용하지 않는다. 동일 원고의 이야기체·질문·숫자·외래어를 비교하고 실제 청취로 발음, 억양, 누락, 반복, 호흡을 확인한다. 긴 영상 전환은 샘플 청취 결과를 먼저 반영한다. 생성·웹 저장 허가는 YouTube 업로드 허가가 아니다.

## 초기 검증 — 2026-10-11

RTX 4070 Laptop 8GB에서 두 한국어 원고를 1.7B/0.6B로 각각 생성했다. 비교 목록은 `storage/korean-comparison-20261011.json`. 1.7B는 21.48초/24.192초 음성을 27.83초/30.62초에 생성했고 PyTorch 최대 할당은 약 4701MB였다. 0.6B는 25.8초/32.904초 음성을 31.83초/46.12초에 생성했다. 시간은 모델 최초 다운로드·로딩을 제외하며 다른 원고/부하에서는 달라진다. 작업 완료 후 GPU 메모리 해제를 확인했다.

SSO/CSRF, 외부 API 명시 선택, 원본 덮어쓰기 방지, 중복 요청, 청취 기록, 클라이언트 해시 검증 테스트 7건과 기존 제작 규칙 3건, Story 12건 및 원본 메타데이터 보존 회귀 1건이 통과했다. 실제 VideoFactory 클라이언트가 기존 테스트 음성을 재생성 없이 받아 동일 해시/작업 ID를 보존했다. 웹에서 모델별 샘플 재생을 확인했다. 자연스러운 말투와 최종 목소리 선택은 사용자 청취 대기다.

최초 다운로드 방식을 변경하면서 중단한 1건은 실패 기록으로 보존하고 새 작업으로 완료했다. 현재 다운로드는 HF_HUB_DISABLE_XET=1로 일반 HTTP 캐시를 사용한다. GitHub push는 완료했으나 Actions 배포 단계가 exit code 1로 실패하여 자동 배포 성공으로 기록하지 않는다. 홈서버에서 직접 Compose 배포·Nginx 검증과 웹 접속을 확인했다.


추가로 1.7B 이야기 원고의 끝 인사 추가 의심을 자동 전사에서 발견해 원고 준수 지시를 보강했다. 새 비교본 `49a4d8810d33434bb6313527f8cf6083`은 20.184초, 생성 25.55초, GPU 최대 4589MB이며 자동 전사에서 문장부호·공백을 제외한 원고가 일치했다. 이 지시를 로컬 기본 스타일에 반영했다. 자동 전사는 실제 발음·자연스러움 청취 승인을 대체하지 않는다. 비교 샘플은 총 5개이고 개별 자동 검사 메모는 웹에 표시한다. 기존 원고 및 초기 실패 기록은 보존한다.


## 남녀 목소리 설계 비교 — 2026-10-11

사용자는 기존 1.7B 시험 음성을 긍정적으로 평가했으며, 더 자연스러운 한국어 말투를 직접 고르기 위해 남성 5종·여성 5종 비교를 요청했다. `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`을 추가하고 `/gumatts/#voices`에서 동일 원고·동일 loudnorm 기준의 후보를 비교한다. M1–M5/F1–F5 설계 문구는 `voice_profiles.py`, 비교 작업 목록은 `storage/voice-comparison-20261011.json`에 보존한다. 지정한 성별·톤은 설계 목표이며 실제 자연스러움을 청취 승인한 것으로 간주하지 않는다.

API 모델 `qwen-design-1.7b`는 voice=M1–M5 또는 F1–F5를 사용한다. VoiceDesign은 `generate_voice_design`을 호출하며 CustomVoice의 Sohee와 구분한다. 전체 설계 지시·시드·모델 revision을 결과에 보존한다. 후보 표시 버튼은 해당 샘플의 청취 메모에만 저장하고 채널 기본 음성을 바꾸지 않는다. 같은 설명만으로 모든 원고에서 음색이 완전히 고정된다고 보장하지 않는다. 최종 선택 후 장문·문단 간 일관성을 별도 검증한다. 기존 Sohee/Zephyr와 결과물은 보존한다.


검증 결과: 비교본 10개 모두 생성 완료(17.472–22.680초), 생성 시간 22.32–31.48초, GPU 최대 할당 4508–4662MB. 모든 최종 비교본의 자동 전사가 문장부호·공백 제외 원고와 일치했고 MP3 디코드 및 원본 결과 해시를 검증했다. F5 v1은 한 구절의 전사 차이가 있어 원본을 보존하고 seed 43의 v2로 재생성해 재검증했다(나머지 seed 42). 자동 전사는 실제 청취 승인이 아니다. 원본 목록 `storage/voice-comparison-20261011-v1.json`, 최종 목록 `storage/voice-comparison-20261011.json`, 검사 요약 `storage/verification/voice-design-summary.json`.

서비스 테스트 9건과 브라우저 남성 M1·여성 F1의 끝까지 재생을 확인했다. 외부 TTS API 호출 없이 로컬 생성했다. 코드 04877cb의 GitHub Actions는 실패했고, HomeServer Compose 빌드·배포와 인증된 웹 비교 화면에서 동작을 확인했다. 이후 사용자 확정으로 쇼츠 F4 / Story·롱폼 M5를 제작 기준으로 적용했다.


## 쇼핑쇼츠 단일 생성 운영 방식

- 고정 참조: `storage/fixed-voices/F4-dates-v1/reference.wav`와 `reference.json`.
- 참조 SHA256: `c5c7d003d5292bbe7e0d66dd7b3ebae8e471f9643084529b48928765b96c93ef`.
- 원본은 대추야자 최초 F4 CUT7이다. 복제한 결과를 다시 참조로 넣는 세대별 복제는 하지 않는다.
- 전체 원고를 한 요청으로 생성하고 원본 WAV·보정 MP3·작업 ID를 보존한다. 문장 경계 정렬은 영상·자막 편집에 사용하며 최종 내레이션은 연속 마스터를 사용한다.
- 자동 대본 대조에서 추가 발화·누락이 나오면 통과시키지 않는다. 숫자의 표기와 실제 낭독 차이는 명시적으로 정규화하며 판단이 불확실한 발음은 청취 검토 대상으로 남긴다.
- 2026-10-11 운영 경로는 GumaDdanjit의 단일 생성 인계 스크립트다. 기존 컷별 자동 렌더 경로를 새 제작에 사용하지 않는다. 등록된 참조 비교용 API 경로로 전체 원고를 생성하며 `test` 프로젝트 표시는 모델 품질 승인과 별개인 기술적 라우팅 값이다.
- Story·롱폼은 Gemini Flash / Zephyr, 이야기쇼츠 F4 경로는 유지한다. 기존 테스트 결과·배포 이력은 과거 검증 기록이며 새 단일 생성 전체 파이프라인 검증으로 재사용하지 않는다.

근거: [Qwen 공식 Voice Design then Clone](https://github.com/QwenLM/Qwen3-TTS#voice-design-then-clone).


이전 2026-10-12 Story 화자 시험 기록(최신 Gemini Zephyr 채택으로 폐기된 기본값): 로컬 `qwen-clone-1.7b` / `M5-fixed-v1`을 기본으로 사용한다. 선정된 M5 비교 작업 `abb9d177a65344ada1587cafeb817c99`의 원본 WAV와 대본을 불변 참조로 등록한다. 컷별 생성·보관·수정 원칙을 유지하며 기준 WAV SHA256과 참조 대본 SHA256까지 캐시 키와 검수에 포함한다. VoiceDesign으로 컷마다 새 화자를 설계하지 않는다. `produce_local_cuts.py`는 제작 폴더의 `voice-settings.json`을 읽고 모든 컷에 동일 참조를 확인한다. 승진 영상 v4 제작 원본·정확한 도구 스냅샷·음색 비교 샘플·검수는 `storage/story/productions/promotion-v4`에 보존한다. 자동 화자 유사도·전사·음량 검사는 실제 청취나 사용자 승인과 구분한다.

2026-10-12 최신 사용자 채택: Story·롱폼 기본은 Gemini Flash TTS / Zephyr이며 로컬 TTS를 사용하지 않는다. 공통 서비스와 명시적 allow_cloud=true, 구간별 저장·정상 구간 재사용을 유지한다. 한도 부족 시 Lite·로컬로 자동 전환하지 않는다. 쇼핑·파생 이야기쇼츠·X 정책은 변경하지 않는다.

- 2026-10-17 Sohee 음량 보정: 희소한 자음 피크 때문에 정적 게인만으로 평균 음량이 부족하면 최대 8dB 이내의 피크 제한(자동 증폭 끔, attack 5ms/release 50ms, 지연 보상) 후 측정 기반 고정 게인을 적용한다. 원본은 보존하고 전후 LUFS·true peak·보정본 해시를 기록한다. 한도를 넘는 원본·무음·클리핑은 계속 실패 처리하며 속도·피치는 변경하지 않는다.
