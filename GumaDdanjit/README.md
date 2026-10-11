# GumaDdanjit — 구마의 딴짓 통합 제작실

- 2026-10-11 사용자 최종 채택: 쇼핑쇼츠(Food·Tech·Living)는 대추야자 v11 방식으로 제작한다. 최초 F4 합성 원본 CUT7에서 고정한 F4-dates-v1 참조 WAV·대본·SHA256을 GumaTTS Qwen 1.7B Base(qwen-clone-1.7b)에 넣어 전체 대사를 한 번에 생성한다. 컷별 독립 생성은 하지 않는다. 발화 경계를 대본과 대조해 영상·자막을 맞추고 최종 음성은 분할 재접합하지 않은 연속 마스터를 사용한다. 피치·배속 변경이나 지원되지 않는 Base style/instruct로 말투를 조정하지 않는다. 원본·새 버전·참조 및 마스터 해시·작업 ID·정렬 근거를 보존한다. 모든 컷의 무음·잘림·발음·음량·BGM 대비와 전 프레임 로고를 검수하고 실제 청취 여부를 별도로 기록한다. 기존 5곡 BGM은 일정한 음량으로 유지하며 교체 작업에서는 기존 선택 곡을 보존한다. Story·롱폼 M5와 이야기쇼츠 F4 정책은 유지한다. 음성 방식 채택을 향후 영상의 자동 업로드·공개 승인으로 간주하지 않는다.
- URL: https://home.guma3d.com/gumaddanjit/
- 홈서버 경로: `D:\TheGumaLab\GumaDdanjit`
- 컨테이너: `GumaDdanjit_app`, HTTP 8089, 단일 FastAPI/ASGI 프로세스.
- GumaShop(쇼핑 쇼츠) `/shorts/`, GumaStory(출퇴근 이야기·롱폼) `/story/`, GumaX(실험적인 고퀄 영상) `/shop/`을 공통 메뉴·검색·결과물 보관함으로 통합한다. 세 개의 기존 서버로 프록시하는 구조가 아니라 모듈을 한 실행 환경에서 구동한다.
- 독립적인 기존 ID·버전·검수 이력은 유지한다. 데이터는 `storage/{shorts,story,shop}`에 보존한다. 웹은 공통 디자인의 읽기 전용 제작 보관함으로 리소스·이미지 콘셉트·완성 영상을 버전별로 보여준다. 대본·출처·참조 음성도 리소스에 포함한다. 피드백·수정 요청·제작/공개 승인은 Codex 대화로 받으며 웹 입력 기능은 제공하지 않는다.
- 모든 음성은 별도 공통 추론 서비스 GumaTTS를 사용한다. 쇼핑쇼츠 고정 참조 F4-dates-v1 / 이야기쇼츠 F4 / Story·롱폼 M5. 유료 API 자동 대체 없음.

## 실행

웹 UI는 `static/archive.{html,css,js}`, 읽기 전용 데이터 정규화는 `archive.py`를 사용한다. `/api/archive`는 기존 저장소를 수정하지 않고 세 공간의 버전·미디어 링크를 반환한다. 기존 쇼츠 아이템·Story 영상/대본 링크도 같은 화면에서 열리며 원본 미디어·공개 상품 모음·제작용 API·SSO 경계는 유지한다. 이전 피드백 기록은 보존하지만 피드백 제출 API는 등록하지 않는다.

```powershell
cd D:\TheGumaLab\GumaDdanjit
docker compose up -d --build
docker exec GumaDdanjit_app python -m pytest tests -q
```

환경변수: `GEMINI_API_KEY`(기존 생성 작업용, .env 비밀), `DDANJIT_AUTH_URL`(Index /auth), `DDANJIT_WORKER`(1=제작 대기열 실행, 0=이관 검증), `GUMADDANJIT_SHORTS_STORAGE`, `GUMASTORY_STORAGE`, `GUMASHOP_STORAGE`, `GUMASHOP_LEGACY`, `GUMATTS_URL`. 호스트 저장소는 `/data`, 과거 영상 제작 명령의 `/app/storage`는 `/data/shorts`로 연결한다. 토큰과 모델은 GumaTTS에서 유지한다. 로컬 독립 검증 시 `DDANJIT_DATA`로 시험 폴더를 지정할 수 있다.

## 인증·링크 보존

Index SSO를 서비스 경계에서 검사하고 모든 쓰기는 동일 Origin을 요구한다. Story/Shop의 기존 쓰기 헤더·충돌 검사는 유지한다. 공개 상품 모음 `/shorts/products`의 GET/HEAD만 비인증 공개하며 제작 파일·DB·API는 공개하지 않는다. 원본 동영상은 버퍼에 적재하지 않고 Range/스트리밍으로 응답한다.

## 이관과 복구

`scripts/migrate.py`는 기존 세 저장소를 삭제하지 않고 복사한다. SQLite backup API와 integrity_check/논리 레코드 비교, 원본 파일별 SHA256 검증을 사용한다. 최종 이관은 기존 서버의 쓰기를 멈춘 후 `python scripts/migrate.py --verify`로 수행한다. 증거는 `backups/migration-verified.json`에 보존한다.

기존 폴더와 컨테이너 이미지는 복구용으로 보존한다. 롤백 시 먼저 GumaDdanjit의 새 작업을 중지하고 이관 이후 새 데이터도 백업한다. 그 후 보관된 기존 Compose 파일로 세 서비스를 시작하고 Nginx 이전 설정을 복원한다. 새 통합 데이터가 생긴 뒤 무작정 과거 저장소로 되돌리지 않는다.

## 제작 명령

기존 쇼츠 Python 명령의 `app.core.*` 모듈 경로는 유지되며 실행 컨테이너만 GumaDdanjit_app으로 변경한다. Story 명령은 `scripts/story/`에서 실행한다. 새 제작 디렉터리는 `/data/story/productions/<new-version>`이며 음성은 M5로 생성한다. 과거 제작 스크립트의 기록은 과거 버전을 재작성하는 허가가 아니다.

승진 영상 v2는 대본 v5·v1 음성을 보존하는 화면 수정본이다. `prepare_promotion_v2.py`의 65개 상황 계획을 내장 ImageGen에서 최신 캐릭터 원본을 참조해 각각 생성한다. 레퍼런스 원본을 최종 컷으로 반복하지 않는다. 실제 프롬프트·참조 및 교정 이력은 제작 폴더의 `generation-prompts.json`, `generation-corrections.json`에 보존한다. 표시 자막은 `display_captions.py`에서 낭독 원문과 분리해 숫자로 변환하며 Pretendard SemiBold·얇은 단일 외곽선을 사용한다.

제작 도구(`revise_promotion_v2.py`, `display_captions.py`, `compose_longform.py`, `review_promotion_v2.py`, `publish_promotion_v2.py`)를 제작 폴더의 `tools/`에 보관한 뒤 컨테이너에서 실행한다. 조립은 `revise_promotion_v2.py <제작폴더>`, 출력은 같은 명령에 `--render`를 붙인다. `review_promotion_v2.py <제작폴더>`는 원본 음성 해시·숫자 자막·전체 프레임 로고·챕터·디코딩을 검사한다. 출력된 114개 화면과 숫자 자막을 실제 시각 검수한 후에만 검수 상태를 기록하고 `publish_promotion_v2.py <제작폴더>`와 `Store('/data/story').ingest()`로 웹에 등록한다. 검수 전·기존 버전 덮어쓰기 등록은 거부한다. 기존 영상의 음성 재사용을 신규 TTS 생성이나 실제 전편 청취 완료로 기록하지 않는다.

승진 v3는 `prepare_promotion_v3.py`로 자연스러운 도입과 화면 안내 제거를 준비한 뒤 `produce_local_cuts.py`로 로컬 M5 음성을 컷별 생성·보관한다. 원문 해시·모델·프로필·음성 해시가 같은 정상 컷은 이전 제작 폴더에서 재사용한다. 실패 테이크는 보존하며 모델이나 유료 API로 자동 대체하지 않는다. `render_promotion_v3.py`는 음성 길이로 타임라인을 재계산하고 얇은 숫자 자막·최종 레이어 로고를 합성한다. Story의 기본은 배경음악 없음이며 깨끗한 음성 원본에서 출력한다. `retime_promotion_v3.py`로 완성 음성 기준 대본 시간표를 새 버전으로 저장한다. `review_promotion_v3.py`의 컷별 원본/보정/최종 음량·파형 대조, 숫자 자막, 전체 프레임 로고 검사와 완성 장면 시각 검수·전사 대사 대조 후 `publish_promotion_v3.py`와 `Store.ingest()`로 웹에 등록한다. 전사 대조·기술 검사와 실제 청취·사용자 승인은 별도로 기록한다.

전사 검수는 GumaTTS의 CPU `faster-whisper==1.2.1`과 로컬 turbo 캐시를 사용한다. `audit_promotion_voice.py` 결과를 최종 `voice-manifest.json`의 작업 ID·해시와 대조하고, 필요하면 `audit_processed_cuts.py`로 실제 트림 음성을 재검사한다. 전사 표기 차이는 근거와 함께 별도 기록하고 `summarize_promotion_asr.py`에서 숫자·대사 차이를 확인한다. 렌더 재시도는 `--encode-only`로 준비된 입력 해시를 검증해 재사용하며 정적 로고는 단일 프레임의 repeatlast로 유지한다. 음성과 대본·출력 검수를 다시 생성 작업으로 대신하지 않는다.

## 2026-10-11 이관 검증

- 쇼츠 9,968개 / 이야기 990개 / 쇼핑 2,535개: 총 13,493개 파일, 약 15.68GiB. 원본 파일 SHA256 전수 일치, 두 SQLite DB의 무결성·전체 레코드 일치 확인. 증거는 `backups/migration-verified.json`.
- 인증·CSRF·편집 충돌·모듈 링크·Range 스트리밍·실제 FFmpeg 콘티 렌더링을 포함한 자동 검사 6개 통과. 브라우저에서 세 작업실·통합 보관함·기존 영상 재생 확인.
- 기존 실행 컨테이너는 종료·제거하고 Compose는 `docker-compose.retired.yml`로 보관한다. 원본 데이터와 이미지는 복구용으로 유지한다. 기존 주소는 새 서비스로 리디렉션한다.
- 유료 Veo/이미지 생성은 이관 검증에 사용하지 않았다. YouTube 업로드·공개 상태 변경 없음.


2026-10-12 Story 화자 일관성 개선: 로컬 `qwen-clone-1.7b` / `M5-fixed-v1`을 기본으로 사용한다. 선정된 M5 비교 작업 `abb9d177a65344ada1587cafeb817c99`의 원본 WAV와 대본을 불변 참조로 등록한다. 컷별 생성·보관·수정 원칙을 유지하며 기준 WAV SHA256과 참조 대본 SHA256까지 캐시 키와 검수에 포함한다. VoiceDesign으로 컷마다 새 화자를 설계하지 않는다. `produce_local_cuts.py`는 제작 폴더의 `voice-settings.json`을 읽고 모든 컷에 동일 참조를 확인한다. 승진 영상 v4 제작 원본·정확한 도구 스냅샷·음색 비교 샘플·검수는 `storage/story/productions/promotion-v4`에 보존한다. 자동 화자 유사도·전사·음량 검사는 실제 청취나 사용자 승인과 구분한다.
