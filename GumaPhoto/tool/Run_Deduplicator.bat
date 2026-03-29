@echo off
title GumaPhoto - Local Duplicate Photo Remover
echo [ GumaPhoto Local Tool ]
echo.

if "%~1"=="" (
    python deduplicate_phash.py
) else (
    echo Target Folder: %~1
    python deduplicate_phash.py "%~1"
)
pause
