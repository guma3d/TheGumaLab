# GumaStory

구마의 딴짓 롱폼을 위한 캐릭터·리소스·대본 작업실.

- 운영 주소: https://home.guma3d.com/gumastory/
- 별도 호스트: gumastory.guma3d.com (Nginx 경로 준비; Cloudflare DNS/ingress는 별도 확인)
- TheGumaLab 대시보드에서 GumaStory 카드로 접근. 기존 홈서버 SSO 로그인 필요.
- 프로젝트: `D:\TheGumaLab\GumaStory`, 컨테이너 `GumaStory_app`, 포트 8087.

## 기능

- 4개 캐릭터의 각도·표정·상황 레퍼런스, 이미지/음성/영상 파일 업로드와 원본 다운로드.
- 캐릭터·분류·상태·검색 필터, 검토 승인/수정 필요, 메모·태그·보관/복원.
- 캐릭터 기준 이미지 선택과 이름·성격 메모. 이미지 원본·생성 프롬프트·참조·SHA256 보존.
- 시간 구간별 내레이션·화면·출처·리소스 연결, 대본 새 버전 저장·이전 버전 조회·Markdown 내보내기.
- 대본 읽기 전용 주소 `/gumastory/scripts/<id>/<version>`: 시간대별 목차, 전체 내레이션, 접을 수 있는 연출·출처, 이전 버전 링크. 로그인 이후에도 선택한 버전 주소를 유지한다. 편집 직접 링크는 `/gumastory/?script=<id>&version=<version>`.
- 완성 영상은 `/gumastory/watch/<asset-id>`에서 재생한다. MP4 다운로드, 실제 음성 길이에 맞춘 구간 탐색, 한국어 자막, 내레이션 단독 재생, 원본 대본 버전과 음악 출처를 함께 보관한다. 해당 대본 읽기 페이지에도 영상 링크를 표시한다.
- 승진 주제 20분 구성 초안 포함. 대본 내용은 조사와 작성 전이며 완성 원고로 표시하지 않는다.
- 이미지 생성·TTS·렌더·YouTube 업로드를 웹에서 자동 실행하지 않는다. 생성한 결과를 관리하는 서비스다.
- 승인된 대본의 문단별 음성 제작·고정 일러스트/차트 편집은 `scripts/produce_narration.py`, `compose_longform.py`, `render_longform.py`를 사용한다. TTS와 FFmpeg/BGM 작업은 기존 VideoFactory 런타임을 사용하며, API 키는 해당 런타임 환경변수에서만 읽는다. 원본 음성·화면·타임라인·출처와 완성본은 버전 폴더에 보존한다. 자막은 문단 음성 경계에 맞추고 문단 내부 시간은 읽기 길이 추정임을 기록한다. 기술 검사와 실제 청취 검수를 구분한다.

## 실행과 배포

```powershell
cd D:\TheGumaLab\GumaStory
docker compose up -d --build
docker compose ps
```

환경변수: `GUMASTORY_AUTH_URL`(기존 Index `/auth`, compose 기본값 제공), `GUMASTORY_STORAGE`(기본 storage), `TZ`(Asia/Seoul). 별도 API 키나 비밀값이 필요하지 않다.

자동 배포는 main push 후 `.github/workflows/deploy.yml`에서 GumaStory 변경을 감지한다. 실패 원인을 확인하고 필요시 위 로컬 배포 명령을 사용한다. Nginx 변경 후 `docker exec HomeServer_Nginx nginx -t` 및 `nginx -s reload`.

## 데이터 보존

`storage/assets/` 원본, `imports/` 생성 메타데이터, `thumbs/` 웹 미리보기, `gumastory.sqlite3` 검토·프로필·대본 버전. SQLite와 원본은 컨테이너 교체 후에도 bind mount에 남는다. 대형 데이터는 Git에 넣지 않는다.

`python scripts/backup.py`로 원본·메타데이터·SQLite 일관 스냅샷을 버전 ZIP에 보관한다. 기본 백업은 storage/backups이며 같은 디스크 장애까지 보호하지는 않는다. 외장/다른 서버 복사는 별도 운영한다. 삭제·복원은 원본 백업 확인 후 수행한다.

ImageGen 신규 결과는 `storage/assets/<unique-id>.png`와 `storage/imports/<unique-id>.json`으로 저장하면 다음 라이브러리 새로고침 때 등록된다. ID·파일명은 고유해야 하며 파일을 덮어쓰지 않는다. JSON에 id, file, title, character_id, kind, version, prompt, reference, tool, status를 남긴다.

`python scripts/export_catalog.py`는 생성 프롬프트·원본 파일명·해시를 `reference-catalog.json`으로 내보낸다. 이 작은 카탈로그는 Git에 보존하고 실제 이미지·검토 데이터는 홈서버 저장소와 ZIP 백업에 보존한다. 카탈로그만으로 이미지 원본을 복원할 수는 없다.

## 검증

```powershell
docker compose run --rm -v D:/TheGumaLab/GumaStory/tests:/app/tests gumastory python -m pytest tests -q
```

SSO 차단, CSRF, 원본 보존과 버전 증가, 잘못된 업로드, 대본 동시 수정 충돌, 시간 구간 검증, 리소스 연결을 검사한다. 테스트 인증 우회는 테스트 함수 인자로만 제공하며 운영 환경변수로 활성화할 수 없다.

## 초기 컬렉션 (2026-10-10)

캐릭터별 15장(각도 6, 표정 4, 상황 5), 총 60개의 서로 다른 1672×941 PNG를 보관한다. 기존 스타일 연구 4장과 보관함의 이전 시안 9장까지 총 73개 리소스다. 새 이미지는 사용자 검토 전이며, 장보기 컷의 생성 가격표 등은 검토 메모를 확인한다.

`python scripts/audit_references.py`로 수량·분류·해상도·중복 해시를 확인한다. 결과와 웹 검수 기록은 `storage/verification/`에 저장한다. 기능 테스트 9건 통과, 인증된 공개 주소에서 필터·원본 상세·대본 v2 저장과 v1 보존을 확인했다. 브라우저에서 확인한 폭은 750px이며, 390px 요청은 도구에서 적용되지 않아 실제 휴대폰 검수로 간주하지 않는다.

홈서버 직접 빌드와 정상 컨테이너 상태는 확인했다. GitHub Actions 자동 배포는 실패했으며 상세 로그는 GitHub 인증이 없어 원인을 확정하지 못했다. 로컬 배포 성공과 자동 배포 성공을 구분한다.
