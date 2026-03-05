FROM python:3.9-slim

# 빌드 중 비대화형 모드 설정
ENV DEBIAN_FRONTEND=noninteractive

# 시스템 업데이트 및 FFmpeg 설치
RUN apt-get update && apt-get install -y --fix-missing \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
# nvidia-cublas-cu12, nvidia-cudnn-cu12: pip로 CUDA 런타임 라이브러리 제공 (apt repo 불필요)
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir \
    Flask>=3.0.0 \
    yt-dlp>=2024.0.0 \
    faster-whisper>=1.0.0 \
    requests \
    nvidia-cublas-cu12 \
    nvidia-cudnn-cu12

# LD_LIBRARY_PATH에 pip 설치된 CUDA 라이브러리 경로 추가
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.9/site-packages/nvidia/cublas/lib:/usr/local/lib/python3.9/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH

# 빌드 시 Whisper turbo 모델 미리 다운로드 (컨테이너 시작 시 다운로드 방지)
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('turbo', device='cpu', compute_type='int8')"

# 애플리케이션 파일 복사
COPY Server.py .
COPY extract_transcript.py .
COPY YoutubeAnalyzer.html .

# 디렉토리 생성
RUN mkdir -p Temp_Audio Scripts Logs

# 포트 개방
EXPOSE 5000

# 환경 변수
ENV FLASK_APP=Server.py
ENV PYTHONUNBUFFERED=1

# 애플리케이션 실행
CMD ["python", "Server.py"]
