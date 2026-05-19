# Reptile Quiz Reports

초등학교 3학년 발표용 파충류 탐구 보고서 작업 패키지입니다.

## 폴더 구조

- `tools/`
  - `generate_reptile_pdfs.py`: 4페이지 버전과 공통 레이아웃/폰트/이미지 도구
  - `generate_reptile_pdfs_detailed.py`: 최종 7페이지 상세 보고서 생성 도구
- `assets/curated_overrides/`
  - 자동 검색 대신 직접 고정한 핵심 특징 이미지
- `outputs/pdfs/`
  - 최종 PDF 14개
- `outputs/qa/`
  - 전체 QA 차트와 수정 집중 확인 차트
- `reptile_reports/`
  - 지도 데이터 캐시. 실행 시 이미지 캐시도 이곳에 생성됩니다.

## 다시 생성하기

```powershell
cd E:\Codex\reptile_quiz
python -m pip install -r requirements.txt
python .\tools\generate_reptile_pdfs_detailed.py
```

생성 결과는 `reptile_reports_detailed/`에 만들어집니다. 기존 최종본은 `outputs/pdfs/`에 따로 보관했습니다.

## 최종 구성

- 14종 각각 7페이지
- TV 표시용 가로형 PDF
- 페이지당 이미지는 1장만 사용
- 지도, 사는 지역, 먹이, 특징, 퀴즈, 정답 설명 구조
- 특징이 잘못 보였던 7종은 `assets/curated_overrides/`의 고정 이미지 사용

## 메모

이 스크립트는 Wikimedia Commons 검색 API와 일부 외부 이미지 URL을 사용합니다. 이미 받은 핵심 수정 이미지는 로컬에 포함해 두었지만, 전체 보고서를 처음부터 다시 만들 때는 네트워크 연결이 필요할 수 있습니다.
