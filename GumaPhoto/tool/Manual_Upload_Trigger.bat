@echo off
chcp 65001 >nul

echo ========================================================
echo   GumaPhoto Manual Upload Trigger Pipeline
echo ========================================================
echo.
echo [INFO] This script will immediately trigger the AI
echo        processing pipeline for any new photos copied 
echo        into the data\uploads_raw folder.
echo.
pause

echo.
echo Triggering background Docker pipeline...
docker exec gumaphoto_app python -c "import sys, os; sys.path.append('/app'); from core.events import publish_event; publish_event('FileUploaded', {'source': 'manual_script_trigger'})"

echo.
echo SUCCESS! Payload delivered to Celery Workers.
echo Photos will now be moved to 'organized' and indexed.
echo Check the web UI [System] tab for live progress.
echo.
pause
