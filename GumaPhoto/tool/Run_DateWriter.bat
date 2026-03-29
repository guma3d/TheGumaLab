@echo off
rem CWD Lock Release
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Local Tool : Date Metadata Injector
echo ========================================================
echo.

if "%~1"=="" GOTO NO_ARGS

echo Launching Date Injector with Target(s)...
python Run_DateWriter.py %*
GOTO END

:NO_ARGS
python Run_DateWriter.py

:END
pause
