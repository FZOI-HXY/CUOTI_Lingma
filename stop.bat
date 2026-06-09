@echo off
chcp 65001 >nul 2>&1

REM Stop all services
echo.
echo Stopping all services...
echo.

tasklist | findstr /i "python.exe" >nul 2>&1
if errorlevel neq 0 (
    echo No Python processes running
    goto END
)

echo Found Python processes:
echo.
tasklist | findstr /i "python.exe"
echo.

echo Stopping all Python processes...
taskkill /F /IM python.exe >nul 2>&1

if errorlevel equ 0 (
    echo Processes stopped
) else (
    echo Failed to stop processes
)

:END
echo.
echo Done.
pause
exit /b 0
