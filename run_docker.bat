@echo off
cd /d "%~dp0"
echo Starting ASTRAM AI Docker build...
docker compose up --build
pause
