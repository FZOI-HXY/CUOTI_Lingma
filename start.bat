@echo off
setlocal enabledelayedexpansion
chcp 936 >nul 2>&1

REM ============================================================
REM Cuoti Management System - Launcher
REM ============================================================

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "PROJECT_ROOT=%SCRIPT_DIR%"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "VENV_PYTHON=%PROJECT_ROOT%\venv312\Scripts\python.exe"
set "ENV_FILE=%BACKEND_DIR%\.env"
set "API_PORT=8100"

title CuotiSystem Launcher

echo.
echo ============================================================
echo   Cuoti Management System
echo ============================================================
echo.
echo   Project: %PROJECT_ROOT%
echo.

REM === Step 1: Check files ===
echo [1/5] Checking files...

if not exist "%VENV_PYTHON%" (
    echo   [ERROR] Python venv not found
    pause
    exit /b 1
)
echo   [OK] Python OK

if not exist "%BACKEND_DIR%\app\main.py" (
    echo   [ERROR] Backend main.py not found
    pause
    exit /b 1
)
echo   [OK] Backend OK

if not exist "%ENV_FILE%" (
    echo   [WARN] .env not found, copying...
    if exist "%BACKEND_DIR%\.env.example" (
        copy "%BACKEND_DIR%\.env.example" "%ENV_FILE%" >nul
        echo   [OK] .env created
    ) else (
        echo   [ERROR] .env.example not found
        pause
        exit /b 1
    )
) else (
    echo   [OK] Config OK
)

echo.

REM === Step 2: Check port ===
echo [2/5] Checking port %API_PORT%...

netstat -ano | findstr ":%API_PORT% " | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo   [WARN] Port %API_PORT% is in use
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%API_PORT% " ^| findstr "LISTENING"') do (
        set "STALE_PID=%%a"
    )
    if defined STALE_PID (
        echo   Killing PID !STALE_PID!...
        taskkill /F /PID !STALE_PID! >nul 2>&1
        timeout /t 2 /nobreak >nul
    )
    netstat -ano | findstr ":%API_PORT% " | findstr "LISTENING" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [ERROR] Port still in use
        pause
        exit /b 1
    )
)
echo   [OK] Port %API_PORT% available

echo.

REM === Step 3: Start VL Engine ===
set "VL_MODEL_DIR=E:\Program Files\PP_Models\official_models\PaddlePaddle\PaddleOCR-VL-1___6-GGUF"
set "VL_MODEL=%VL_MODEL_DIR%\PaddleOCR-VL-1.6-GGUF.gguf"
set "VL_MMPROJ=%VL_MODEL_DIR%\PaddleOCR-VL-1.6-GGUF-mmproj.gguf"
set "LLAMA_SERVER=%PROJECT_ROOT%\tools\llama-cpp\llama-server.exe"

echo [3/5] Starting VL engine...

if exist "%LLAMA_SERVER%" (
    if exist "%VL_MODEL%" (
        echo   Launching llama-server on port 8101...
        call :start_vl
        echo   [OK] VL engine started (port 8101)
        timeout /t 3 /nobreak >nul
    ) else (
        echo   [SKIP] VL model not found
    )
) else (
    echo   [SKIP] llama-server not found
)

echo.

REM === Step 4: Start backend ===
echo [4/5] Starting backend...

call :start_backend

echo   [OK] Backend started
echo   API docs: http://localhost:%API_PORT%/docs
echo.
echo   Waiting for backend...

for /l %%i in (1,1,10) do (
    curl -s http://localhost:%API_PORT%/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] Backend ready!
        goto backend_ready
    )
    timeout /t 2 /nobreak >nul
)
echo   [WARN] Backend may not be ready yet

:backend_ready

echo.

REM === Step 5: Start client ===
echo [5/5] Starting client...

set "TAURI_EXE=%PROJECT_ROOT%\APP\src-tauri\target\release\cuoti-client.exe"
if exist "%TAURI_EXE%" (
    start "" "%TAURI_EXE%"
    echo   [OK] Tauri client started
) else (
    if exist "%FRONTEND_DIR%\main.py" (
        echo   [INFO] Tauri not found, starting PyQt6...
        call :start_frontend
        echo   [OK] PyQt6 frontend started
    ) else (
        echo   [ERROR] No frontend available
    )
)

echo.
echo ============================================================
echo   System started successfully!
echo ============================================================
echo.
echo   Endpoints:
echo     - API docs:   http://localhost:%API_PORT%/docs
echo     - Health:     http://localhost:%API_PORT%/health
echo.
echo   To stop: close the cmd windows
echo.
echo ============================================================
echo.
echo Press any key to close this launcher...
pause >nul
exit /b 0


REM === Subroutines ===

:start_vl
start "VL-Engine" /min "" "%LLAMA_SERVER%" -m "%VL_MODEL%" --mmproj "%VL_MMPROJ%" --port 8101 --host 0.0.0.0 --ctx-size 4096 --temp 0 -ngl 0
goto :eof

:start_backend
cd /d "%BACKEND_DIR%"
start "Backend-FastAPI" "" "%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port %API_PORT%
goto :eof

:start_frontend
cd /d "%FRONTEND_DIR%"
start "Frontend-PyQt6" "" "%VENV_PYTHON%" main.py
goto :eof
