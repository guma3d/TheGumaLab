@echo off
rem 드래그 앤 드롭 폴더 잠김 방지용 CWD 락 해제
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Local Tool : GPS and Date Viewer
echo ========================================================
echo.

if "%~1"=="" GOTO NO_ARGS

echo Launching Viewer with Target(s)...
python Run_GPSandDateViewer.py %*
GOTO END

:NO_ARGS
python Run_GPSandDateViewer.py

:END
pause
