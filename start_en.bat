@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM ============================================================
REM Cuoti Management System - One-click Startup Script (English)
REM Use absolute paths to avoid path issues
REM ============================================================

REM Get script directory absolute path
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Set project paths (use absolute paths)
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "VENV_PYTHON=%PROJECT_ROOT%\venv312\Scripts\python.exe"
set "ENV_FILE=%BACKEND_DIR%\.env"

title Cuoti System Launcher

echo.
echo ============================================================
echo   Cuoti Management System - Startup
echo ============================================================
echo.
echo   Project Root: %PROJECT_ROOT%
echo.

REM Step 1: Check required files
echo [1/5] Checking system files...
echo.

if not exist "%VENV_PYTHON%" (
    echo   ERROR: Python virtual environment not found
    echo   Path: %VENV_PYTHON%
    echo.
    echo   Please create virtual environment and install dependencies first
    pause
    exit /b 1
)
echo   OK: Python environment ready

if not exist "%BACKEND_DIR%\app\main.py" (
    echo   ERROR: Backend main program not found
    echo   Path: %BACKEND_DIR%\app\main.py
    pause
    exit /b 1
)
echo   OK: Backend program exists

if not exist "%FRONTEND_DIR%\main.py" (
    echo   ERROR: Frontend main program not found
    echo   Path: %FRONTEND_DIR%\main.py
    pause
    exit /b 1
)
echo   OK: Frontend program exists

if not exist "%ENV_FILE%" (
    echo   WARNING: .env file not found
    if exist "%BACKEND_DIR%\.env.example" (
        echo   Creating .env from example...
        copy "%BACKEND_DIR%\.env.example" "%ENV_FILE%" >nul
        echo   OK: .env file created
    ) else (
        echo   ERROR: .env.example not found either
        pause
        exit /b 1
    )
) else (
    echo   OK: Configuration file exists
)

echo.
echo   All checks passed!
echo.

REM Step 2: Initialize database if needed
echo [2/5] Checking database...
echo.

if not exist "%PROJECT_ROOT%\cuoti_system.db" (
    echo   Database not found, initializing...
    cd /d "%BACKEND_DIR%"
    "%VENV_PYTHON%" -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine); print('Database initialized')"
    if errorlevel neq 0 (
        echo   WARNING: Database initialization may have failed
    ) else (
        echo   OK: Database initialized
    )
) else (
    echo   OK: Database exists
)

echo.

REM Step 3: Check port 8001
echo [3/5] Checking port 8001...
echo.

netstat -ano | findstr ":8001.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo   WARNING: Port 8001 is already in use
    echo.
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001.*LISTENING"') do (
        echo   Found process PID: %%a
    )
    echo.
    set /p confirm="Stop existing processes and continue? (y/n): "
    if /i "!confirm!"=="y" (
        echo   Stopping processes...
        taskkill /F /IM python.exe >nul 2>&1
        timeout /t 2 /nobreak >nul
        echo   OK: Processes stopped
    ) else (
        echo   Cancelled by user
        pause
        exit /b 0
    )
) else (
    echo   OK: Port 8000 is available
)

echo.

REM Step 4: Start backend service
echo [4/5] Starting backend service...
echo.

cd /d "%BACKEND_DIR%"
start "Backend Service" cmd /k "cd /d %BACKEND_DIR% && %VENV_PYTHON% -m app.main"

echo   Backend starting...
echo   API Docs: http://localhost:8001/docs
echo   Health Check: http://localhost:8001/health
echo.

REM Wait for backend to start
echo   Waiting for backend to be ready...
timeout /t 3 /nobreak >nul

REM Health check
echo   | set /p dummy="   Checking service status..."
for /l %%i in (1,1,5) do (
    curl -s http://localhost:8001/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo OK: Backend service ready!
        goto backend_ready
    )
    timeout /t 1 /nobreak >nul
)
echo WARNING: Backend may not be fully started, but continuing with frontend

:backend_ready
echo.

REM Step 5: Start frontend application
echo [5/5] Starting frontend application...
echo.

cd /d "%FRONTEND_DIR%"
start "Frontend Application" cmd /k "cd /d %FRONTEND_DIR% && %VENV_PYTHON% main.py"

echo   Frontend starting...
echo.

timeout /t 2 /nobreak >nul

echo ============================================================
echo   Startup Complete!
echo ============================================================
echo.
echo   Backend API: http://localhost:8001
echo   API Documentation: http://localhost:8001/docs
echo   Health Check: http://localhost:8001/health
echo.
echo   To stop services:
echo     - Close the console windows, OR
echo     - Run: stop.bat
echo.
echo   Press any key to close this window...
pause >nul
exit /b 0
