@echo off
REM ============================================================
REM  TheGumaLab — Universal deploy script (HomeServer)
REM  Usage:  pull_update.bat ^<ProjectName^> [container_to_restart]
REM  Example: pull_update.bat GumaPhoto gumaphoto_celery
REM           pull_update.bat GumaStockReport
REM ============================================================

setlocal

if "%~1"=="" (
    echo.
    echo Usage: pull_update.bat ^<ProjectName^> [container_to_restart]
    echo.
    echo Available projects:
    echo   GumaPhoto  GumaStockReport  GumaImageAnalyzer
    echo   GumaServerStatus  GumaTube  GumaTutorDoc  Index  Nginx
    echo.
    exit /b 1
)

set PROJECT=%~1
set CONTAINER=%~2
set PROJECT_DIR=D:\TheGumaLab\%PROJECT%

if not exist "%PROJECT_DIR%" (
    echo [INFO] Project directory not found. Syncing repository root first...
    cd /d D:\TheGumaLab || exit /b 1
    git fetch origin main || exit /b 1
    git reset --hard origin/main || exit /b 1
)

if not exist "%PROJECT_DIR%" (
    echo [ERROR] Project directory still not found after sync: %PROJECT_DIR%
    exit /b 1
)

cd /d "%PROJECT_DIR%"

echo [1/3] Fetching latest from origin/main...
git fetch origin main || exit /b 1

echo [2/3] Resetting working tree to origin/main...
git reset --hard origin/main || exit /b 1

echo [3/3] Rebuilding docker compose...
docker compose up -d || exit /b 1

if /I "%PROJECT%"=="Nginx" (
    echo Validating and reloading Nginx...
    docker exec HomeServer_Nginx nginx -t || exit /b 1
    docker exec HomeServer_Nginx nginx -s reload || exit /b 1
)

if not "%CONTAINER%"=="" (
    echo Restarting container: %CONTAINER%
    docker restart %CONTAINER% || exit /b 1
)

echo.
echo === Deploy completed: %PROJECT% ===
endlocal
