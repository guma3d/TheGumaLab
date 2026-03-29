@echo off
chcp 65001 >nul
echo ========================================================
echo   🚀 GumaPhoto 대규모 업로드 이전 원본 사전 전처리기 🚀
echo ========================================================
echo.
echo [기능 1] 동영상 파일(mp4, mov 등)을 깔끔하게 영구 제거합니다.
echo [기능 2] 파일의 이름(예: "IMG_2018-01-15")을 정규식으로 자동 분석하여
echo          누락된 사진 촬영 메타데이터(Exif) 일자를 "영리하게 강제 주입"합니다.
echo          (이미 날짜가 있는 사진은 제외, "일"이 없는 경우는 무조건 01일로 고정)
echo.
echo 하단의 "C:\Users\guma3\Downloads\새 폴더" 등과 같이
echo 처리할 사진들이 들어있는 [최상위 폴더]를 이 창에 드래그하거나 경로를 복사-붙여넣기 하세요!
echo.
set /p TARGET_PATH="폴더 경로 입력: "
echo.

REM 경로의 앞뒤 큰따옴표가 들어오면 자동으로 벗겨냅니다
set TARGET_PATH=%TARGET_PATH:"=%
set TARGET_PATH=%TARGET_PATH:'=%

echo [*] GumaPhoto 컨테이너 내장 ExifTool 가동 중... 
echo     (폴더의 크기와 사진 장수에 따라 시간이 걸릴 수 있습니다)
echo.

docker run --rm -it --env-file "%~dp0..\.env" -v "%TARGET_PATH%:/process" -v "%~dp0..:/app" gumaphoto-gumaphoto:latest python /app/Scripts/preprocess_tool.py

echo.
echo ✅ 전처리가 완료되었습니다! 이제 이 폴더 안의 파일들을 
echo    data\uploads_raw 폴더로 자유롭게 이동시키고 Manual_Upload_Trigger.bat 을 실행하세요!
echo.
pause
