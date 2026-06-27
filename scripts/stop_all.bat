@echo off
chcp 65001 >nul
REM 错题管理系统 - 停止所有服务
REM 仅停止本应用的进程（通过端口识别），不会影响其他 Python 程序

echo.
echo ============================================================
echo   停止所有错题管理系统服务
echo ============================================================
echo.

echo 正在查找错题管理系统服务...
echo.

set "FOUND=0"

REM 检查端口 8100（后端）
netstat -ano | findstr ":8100 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo   发现后端服务 (端口 8100)
    set "FOUND=1"
)

REM 检查端口 8101（VL 引擎）
netstat -ano | findstr ":8101 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo   发现 VL 引擎 (端口 8101)
    set "FOUND=1"
)

if "%FOUND%"=="0" (
    echo   没有运行中的错题管理系统服务
    goto END
)

echo.
set /p confirm="是否停止以上服务? (y/n): "
if /i not "%confirm%"=="y" goto END

echo.
echo 正在停止进程...

REM 停止端口 8100 上的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100 " ^| findstr "LISTENING" 2^>nul') do (
    echo   停止后端进程 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM 停止端口 8101 上的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8101 " ^| findstr "LISTENING" 2^>nul') do (
    echo   停止 VL 引擎 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul

REM 验证端口已释放
netstat -ano | findstr ":8100 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo   端口 8100 仍被占用
) else (
    echo   端口 8100 已释放
)

netstat -ano | findstr ":8101 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo   端口 8101 仍被占用
) else (
    echo   端口 8101 已释放
)

echo   服务已停止

:END
echo.
echo ============================================================
pause
