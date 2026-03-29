@echo off
rem CWD Lock Release
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Local Tool : GPS Geotag Injector
echo ========================================================
echo.

if "%~1"=="" GOTO NO_ARGS

echo Launching Injector with Target(s)...
python Run_GPSWriter.py %*
GOTO END

:NO_ARGS
python Run_GPSWriter.py

:END
pause
