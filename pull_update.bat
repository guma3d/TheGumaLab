cd /d D:\TheGumaLab\GumaPhoto
git fetch origin main
git reset --hard origin/main
docker restart gumaphoto_app
