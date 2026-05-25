# Guma Python Lab Prototype

3분할 Python 학습 앱 프로토타입입니다.

- 왼쪽 위: 강의화면
- 왼쪽 아래: 게임화면
- 오른쪽: 파이썬 코드 화면

## 실행

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython
python .\app\guma_python_lab.py
```

## 현재 범위

- 시즌 1 보물 점수 게임 기반
- 챕터 1~12 버튼 제공
- 챕터별 코드 저장: `user_saves/season_01/chapter_XX/upgrade_zone.py`
- `Play`를 누르면 저장된 코드를 즉시 게임화면에 반영
- 강의자료는 챕터당 최대 10페이지 이하의 가로형 PDF/PNG 구성을 기준으로 함

## 다음 개선 후보

- 실제 교재 PDF/Markdown 뷰어 연결
- 기존 `engine.py`를 앱 패널에 직접 임베드하도록 공통 엔진화
- 에러 메시지 아이 눈높이 변환
- 챕터 완료 체크와 진도 저장
