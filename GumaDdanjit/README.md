# GumaDdanjit — 구마의 딴짓 통합 제작실

- URL: https://home.guma3d.com/gumaddanjit/
- 홈서버 경로: `D:\TheGumaLab\GumaDdanjit`
- 컨테이너: `GumaDdanjit_app`, HTTP 8089, 단일 FastAPI/ASGI 프로세스.
- GumaShop(쇼핑 쇼츠) `/shorts/`, GumaStory(출퇴근 이야기·롱폼) `/story/`, GumaX(실험적인 고퀄 영상) `/shop/`을 공통 메뉴·검색·결과물 보관함으로 통합한다. 세 개의 기존 서버로 프록시하는 구조가 아니라 모듈을 한 실행 환경에서 구동한다.
- 독립적인 기존 ID·버전·검수 이력은 유지한다. 데이터는 `storage/{shorts,story,shop}`에 보존한다. 영상/대본/인물/상품/콘티 편집은 각 제작 모듈, 모든 프로젝트·영상·음성 검색과 재생은 통합 홈에서 제공한다.
- 모든 음성은 별도 공통 추론 서비스 GumaTTS를 사용한다. Food 고정 화자 F1-bright-v2 / 다른 쇼츠 F4 / Story·롱폼 M5. 유료 API 자동 대체 없음.

## 실행

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

## 2026-10-11 이관 검증

- 쇼츠 9,968개 / 이야기 990개 / 쇼핑 2,535개: 총 13,493개 파일, 약 15.68GiB. 원본 파일 SHA256 전수 일치, 두 SQLite DB의 무결성·전체 레코드 일치 확인. 증거는 `backups/migration-verified.json`.
- 인증·CSRF·편집 충돌·모듈 링크·Range 스트리밍·실제 FFmpeg 콘티 렌더링을 포함한 자동 검사 6개 통과. 브라우저에서 세 작업실·통합 보관함·기존 영상 재생 확인.
- 기존 실행 컨테이너는 종료·제거하고 Compose는 `docker-compose.retired.yml`로 보관한다. 원본 데이터와 이미지는 복구용으로 유지한다. 기존 주소는 새 서비스로 리디렉션한다.
- 유료 Veo/이미지 생성은 이관 검증에 사용하지 않았다. YouTube 업로드·공개 상태 변경 없음.

- 2026-10-11 Food 후속 피드백: 너무 차분한 v1보다 조금 더 밝고 경쾌한 친근한 여성 말투를 목표로 F1-bright-v2 참조를 재사용한다. 기존 합성 여성 정체성을 최대한 유지하며 과장된 F4·매 컷 독립 VoiceDesign으로 돌아가지 않는다. Base는 style/instruct를 적용하지 않으므로 실제 참조 생성 경로와 해시를 기록한다. 볼륨 증가·피치 시프트·일괄 배속을 말투 조정으로 대신하지 않는다. v1 원본은 보존하고 실제 청취 전에는 개선·사용자 승인으로 기록하지 않는다.
