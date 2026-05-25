# Guma Python Lab Prototype

3분할 Python 학습 앱 프로토타입입니다.

- 왼쪽 위: 강의화면
- 왼쪽 아래: 게임화면
- 오른쪽: 파이썬 코드 화면

기본 레이아웃은 좌우 50:50, 왼쪽 상하 50:50 고정입니다.
사용자가 화면 분할 비율을 직접 바꾸지 않는 구조입니다.

## 실행

앱은 `tkinter`와 `Pillow`를 사용합니다.

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython
python .\app\guma_python_lab.py
```

## 현재 범위

- 시즌 1 보물 점수 게임 기반
- 챕터 1~12 작은 드롭다운 제공
- 챕터별 코드 저장: `user_saves/season_01/chapter_XX/upgrade_zone.py`
- `Play`를 누르면 저장된 코드를 즉시 게임화면에 반영
- 앱 크롬과 코드 편집기는 Dark 테마
- 강의자료와 게임 화면은 밝고 아기자기한 현재 색상 유지
- 챕터 1 강의자료는 8페이지 PDF/PNG 샘플 구현 완료
- 강의자료는 챕터당 5페이지 안팎을 기본으로 하며 최대 10페이지 이하의 가로형 PDF/PNG 구성을 기준으로 함
- 앱은 `chapter_XX_pNN.png` 페이지 이미지를 우선 표시하고, 없으면 단일 PNG 또는 Markdown 텍스트로 fallback

## 다음 개선 후보

- 챕터 2~3 강의자료 제작
- 챕터 완료 체크와 진도 저장
- 에러 메시지 아이 눈높이 변환
- 기존 `engine.py`와 앱 내 게임 패널의 공통화 여부 검토
