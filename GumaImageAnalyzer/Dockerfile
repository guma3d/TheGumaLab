FROM python:3.9-slim

WORKDIR /app

# OpenCV를 위한 시스템 의존성 설치 (필요한 경우)
RUN apt-get update && apt-get install -y --fix-missing \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    git \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 업로드 디렉토리 생성
RUN mkdir -p uploads

EXPOSE 5000

CMD ["python", "app.py"]
