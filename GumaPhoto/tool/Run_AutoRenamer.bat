@echo off
rem CWD Lock Release
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Local Tool : Auto File Renamer (YYYY-MM_000X)
echo ========================================================
echo.

if "%~1"=="" GOTO NO_ARGS

echo Launching Auto Renamer Engine with Target(s)...
python Run_AutoRenamer.py %*
GOTO END

:NO_ARGS
python Run_AutoRenamer.py

:END
pause
