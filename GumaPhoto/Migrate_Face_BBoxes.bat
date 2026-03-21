@echo off
chcp 65001 >nul
echo ========================================================
echo   [Face BBox Migration Script Runner]
echo ========================================================
echo.
echo Running Docker Exec to patch missing bounding boxes...
echo Please wait. DO NOT CLOSE THIS WINDOW.
echo.

docker exec -it gumaphoto_celery python /app/Scripts/migrate_face_bboxes.py

echo.
echo ========================================================
echo   [DONE] Migration Task Completed. Press any key to exit.
echo ========================================================
pause
