@echo off
echo ============================================================
echo   ASTRAM AI - Bengaluru Traffic Intelligence Platform V1.0
echo ============================================================
echo.
echo Starting server...
cd /d "%~dp0"
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000 --reload
pause
