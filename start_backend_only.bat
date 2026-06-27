@echo off
chcp 65001 >nul 2>&1

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "VENV_PYTHON=%PROJECT_ROOT%venv312\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Python venv not found at: %VENV_PYTHON%
    pause
    exit /b 1
)
if not exist "%BACKEND_DIR%\app\main.py" (
    echo [ERROR] Backend main.py not found at: %BACKEND_DIR%
    pause
    exit /b 1
)

echo.
echo Starting backend service on port 8100...
echo.

start "Backend-FastAPI" /D "%BACKEND_DIR%" "%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8100

echo Backend launcher started. Waiting 5 seconds...
timeout /t 5 /nobreak >nul

echo.
echo Verifying backend health...
curl -sf http://127.0.0.1:8100/health
echo.
echo Done. If you see a JSON response above, it works.
pause
