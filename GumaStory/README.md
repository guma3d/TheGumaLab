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
- 승진 주제 20분 구성 초안 포함. 대본 내용은 조사와 작성 전이며 완성 원고로 표시하지 않는다.
- 이미지 생성·TTS·렌더·YouTube 업로드를 웹에서 자동 실행하지 않는다. 생성한 결과를 관리하는 서비스다.

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

## 검증

```powershell
docker compose run --rm -v D:/TheGumaLab/GumaStory/tests:/app/tests gumastory python -m pytest tests -q
```

SSO 차단, CSRF, 원본 보존과 버전 증가, 잘못된 업로드, 대본 동시 수정 충돌, 시간 구간 검증, 리소스 연결을 검사한다. 테스트 인증 우회는 테스트 함수 인자로만 제공하며 운영 환경변수로 활성화할 수 없다.
