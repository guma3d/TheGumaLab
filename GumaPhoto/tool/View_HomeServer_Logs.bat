@echo off
chcp 65001 >nul
echo ========================================================
echo   [REMOTE] GumaPhoto HomeServer Live Logs Stream
echo ========================================================
echo.
echo Please press "Ctrl + C" to exit.
echo --------------------------------------------------------

ssh HomeServer "cd /d D:\TheGumaLab\GumaPhoto && docker compose logs -f --tail 100"
pause
