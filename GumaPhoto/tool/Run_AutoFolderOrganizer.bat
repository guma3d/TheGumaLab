@echo off
rem CWD Lock Release
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Local Tool : Auto Folder Organizer
echo ========================================================
echo.

if "%~1"=="" GOTO NO_ARGS

echo Launching Auto Organizer with Target(s)...
python Run_AutoFolderOrganizer.py %*
GOTO END

:NO_ARGS
python Run_AutoFolderOrganizer.py

:END
pause
