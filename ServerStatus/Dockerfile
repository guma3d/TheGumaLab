FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성 설치 (필요시)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
RUN pip install flask psutil requests

# 앱 파일 복사
COPY . .

# 포트 개방
EXPOSE 8080

# 실행
CMD ["python", "app.py"]
