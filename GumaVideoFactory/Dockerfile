FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (ffmpeg, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    blender \
    && rm -rf /var/lib/apt/lists/*

# Official LTS build includes OpenImageDenoise (Debian's build omits it).
# Keep the distro package for its tested runtime libraries; PATH selects LTS.
RUN curl -fL --retry 2 https://download.blender.org/release/Blender4.5/blender-4.5.14-linux-x64.tar.xz -o /tmp/blender.tar.xz \
    && echo "9ba871ff2ecd36526b77432745980b7e6664ecd0c7ca11c48849073dcfe06da3  /tmp/blender.tar.xz" | sha256sum -c - \
    && mkdir -p /opt/blender \
    && python -c "import tarfile; tarfile.open('/tmp/blender.tar.xz').extractall('/opt/blender', filter='data')" \
    && ln -s /opt/blender/blender-4.5.14-linux-x64/blender /usr/local/bin/blender \
    && rm /tmp/blender.tar.xz

RUN apt-get update && apt-get install -y --no-install-recommends libsm6 libice6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8085

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]
