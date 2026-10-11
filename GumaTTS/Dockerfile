FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg sox libsndfile1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124 && pip install --no-cache-dir -r requirements.txt
COPY . .
ENV HF_HOME=/models PYTHONUNBUFFERED=1
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8088", "--workers", "1"]
