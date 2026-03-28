cd /d D:\TheGumaLab\GumaPhoto
git fetch origin main
git reset --hard origin/main
docker compose up -d
docker restart gumaphoto_celery
