@echo off
rem CWD Lock Release
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Tool : Unknown Person Face Hunter (Docker)
echo ========================================================
echo.
echo Launching Face Hunter inside docker container...
docker exec -it gumaphoto_app python /app/tool/Run_UnknownFaceHunter.py

echo.
pause
