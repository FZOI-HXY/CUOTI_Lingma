@echo off
chcp 65001 >nul 2>&1

echo.
echo Starting backend service on port 8001...
echo.

cd /d "%~dp0backend"
..\venv312\Scripts\python.exe -m app.main

pause
