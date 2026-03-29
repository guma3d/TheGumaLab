@echo off
rem CWD Lock Release
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Local Tool : Smart Visual GPS Sync
echo ========================================================
echo.

if "%~1"=="" GOTO NO_ARGS

echo Launching Smart GPS Sync with Target(s)...
python Run_SmartGPSSync.py %*
GOTO END

:NO_ARGS
python Run_SmartGPSSync.py

:END
pause
