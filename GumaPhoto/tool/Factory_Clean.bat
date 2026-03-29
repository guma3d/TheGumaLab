@echo off

echo ========================================================
echo   GumaPhoto Factory Clean (Hard Reset) Tool
echo ========================================================
echo.
echo This tool will PERMANENTLY DESTROY all AI database
echo vectors, 3D Map geojson cache, and WebP thumbnail files.
echo (The re-indexing pipeline will NOT be triggered automatically.)
echo.
echo Are you ABSOLUTELY SURE you want to proceed? 
echo If yes, press ENTER to confirm.
pause

echo.
echo [Step 1] Deleting generated WebP thumbnails natively from D:\Pictures\...
del /s /q "D:\Pictures\*_jpg.webp"
del /s /q "D:\Pictures\*_heic.webp"
del /s /q "D:\Pictures\*_png.webp"
del /s /q "D:\Pictures\*_mp4.webp"
del /s /q "D:\Pictures\*_mov.webp"

echo.
echo [Step 2] Deleting 3D Map GeoJSON cache from frontend folder...
if exist "..\frontend\photos_map.geojson" del /q "..\frontend\photos_map.geojson"

echo.
echo [Step 3] Executing DB WIPE directly from local Docker Container...
docker exec -it gumaphoto_app python /app/Scripts/factory_clean.py

echo.
echo Factory Clean process sequence has been fully completed.
pause
