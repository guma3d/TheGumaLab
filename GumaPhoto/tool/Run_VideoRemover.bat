@echo off
rem 드래그 앤 드롭으로 인한 타겟 폴더 변경 불가(잠김) 현상 영구 해제
cd /d "%~dp0"

echo ========================================================
echo   GumaPhoto Local Tool : Mass Video Remover
echo ========================================================
echo.

if "%~1"=="" (
    python remove_videos.py
) else (
    echo Initialized Target Folder: %~1
    python remove_videos.py "%~1"
)
pause
