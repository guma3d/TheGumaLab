# Python 3.11 슬림 버전 사용
FROM python:3.11-slim

# Windows 인코딩 문제를 방지하기 위해 기본 인코딩 UTF-8 설정
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 작업 디렉토리 설정
WORKDIR /app

# 기본 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 실행 (추후 app.py 등으로 변경)
CMD ["python", "app.py"]
