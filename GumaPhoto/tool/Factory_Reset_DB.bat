@echo off
chcp 65001 >nul

echo ========================================================
echo   GumaPhoto 완전 초기화 및 딥러닝 재분석 툴 (Factory Reset)
echo ========================================================
echo.
echo 이 툴은 기존에 학습된 [모든 사진의 데이터베이스]를 폭파시키고,
echo 조직화된(organized) 폴더 내의 모든 사진들을 처음부터 다시
echo 0.0%% 부터 AI 파이프라인(Florence, SigLIP, InsightFace)에 밀어넣습니다.
echo.
echo [주의사항] 
echo - 기존에 유저가 선택했던 피드백 데이터는 원본 사진(EXIF)에 주입되어
echo   안전하게 살아있기 때문에, 재분석이 끝나면 모두 완벽하게 복구됩니다!
echo - 수만 장의 사진인 경우 며칠이 소요될 수 있습니다.
echo.

pause

echo.
echo [SSH] 홈 서버에 접속하여 팩토리 리셋 컨테이너 환경을 호출합니다...
ssh HomeServer "docker exec -it gumaphoto_app python /app/Scripts/factory_reset_db.py"

echo.
echo 모든 과정이 종료되었습니다.
pause
