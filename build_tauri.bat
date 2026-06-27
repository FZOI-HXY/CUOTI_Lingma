@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Cuoti Client (Tauri) - Build Installer
echo ============================================================
echo.

cd /d "F:\CUOTI_Lingma\APP"

echo [1/4] Checking environment...

where rustc >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Rust not found.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('rustc --version') do echo   Rust: %%v

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Node.js not found.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do echo   Node: %%v

if not exist "node_modules" (
    echo   Installing npm dependencies...
    call npm install
    if !errorlevel! neq 0 (
        echo   [ERROR] npm install failed
        pause
        exit /b 1
    )
)
echo   [OK] Environment ready
echo.

echo [2/4] Cleaning previous build artifacts...
if exist "src-tauri\target\release\bundle\nsis" (
    echo   Removing old NSIS bundle...
    rmdir /s /q "src-tauri\target\release\bundle\nsis"
)
echo   [OK] Clean
echo.

echo [3/4] Building Tauri application...
echo   This may take several minutes on first build.
echo.

call npx tauri build 2>&1

if !errorlevel! neq 0 (
    echo.
    echo   [ERROR] Build failed! Check the output above.
    pause
    exit /b 1
)

echo.
echo [4/4] Build output:
echo.

set "NSIS_DIR=src-tauri\target\release\bundle\nsis"
if exist "%NSIS_DIR%" (
    echo   NSIS installer files:
    for %%f in ("%NSIS_DIR%\*.exe") do (
        echo     %%~nxf  ^(%%~zf bytes^)
    )
    echo.
    echo   Location: F:\CUOTI_Lingma\APP\%NSIS_DIR%\
) else (
    echo   [WARN] NSIS bundle directory not found
)

set "EXE_DIR=src-tauri\target\release"
if exist "%EXE_DIR%\cuoti-client.exe" (
    echo.
    echo   Standalone executable:
    echo     cuoti-client.exe
    echo   Location: F:\CUOTI_Lingma\APP\%EXE_DIR%\
)

echo.
echo ============================================================
echo   Build complete!
echo ============================================================
echo.
pause
