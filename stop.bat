@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo   Cuoti Management System - Stop All Services
echo ============================================================
echo.

set "API_PORT=8100"
set "VL_PORT=8101"

REM Stop backend
echo [1/3] Stopping backend (port %API_PORT%)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%API_PORT% " ^| findstr "LISTENING"') do (
    echo   Sending graceful shutdown to PID %%a...
    taskkill /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%API_PORT% " ^| findstr "LISTENING"') do (
    echo   Force killing PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)
echo   [OK] Backend stopped

REM Stop VL engine
echo [2/3] Stopping VL engine (port %VL_PORT%)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%VL_PORT% " ^| findstr "LISTENING"') do (
    echo   Sending graceful shutdown to PID %%a...
    taskkill /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%VL_PORT% " ^| findstr "LISTENING"') do (
    echo   Force killing PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)
echo   [OK] VL engine stopped

REM Stop Tauri client
echo [3/3] Stopping Tauri client...
taskkill /IM cuoti-client.exe >nul 2>&1
echo   [OK] Tauri client stopped

echo.
echo ============================================================
echo   All services stopped.
echo ============================================================
echo.
pause
