@echo off
chcp 65001 >nul
REM 停止所有服务

echo.
echo ============================================================
echo 🛑 停止所有服务
echo ============================================================
echo.

echo 正在查找Python进程...
echo.

tasklist | findstr /i "python.exe" >nul
if %errorlevel% neq 0 (
    echo ℹ️  没有运行中的Python进程
    goto END
)

echo 发现以下Python进程:
echo.
tasklist | findstr /i "python.exe"
echo.

set /p confirm="是否停止所有Python进程? (y/n): "
if /i not "%confirm%"=="y" goto END

echo.
echo 正在停止进程...
taskkill /F /IM python.exe 2>nul

if %errorlevel% equ 0 (
    echo ✅ 已停止所有Python进程
) else (
    echo ⚠️  部分进程可能需要管理员权限才能停止
    echo.
    echo 请以管理员身份运行此脚本,或手动在任务管理器中结束进程
)

:END
echo.

REM 检查端口8000
echo 检查端口8000...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo ⚠️  端口8000仍被占用
    netstat -ano | findstr ":8000"
) else (
    echo ✅ 端口8000已释放
)

echo.
echo ============================================================
pause
