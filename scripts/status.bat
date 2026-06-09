@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM ============================================================
REM 错题管理系统 - 状态检查
REM ============================================================

title 系统状态检查

echo.
echo ============================================================
echo   📊 系统状态检查
echo ============================================================
echo.

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_PYTHON=%SCRIPT_DIR%\venv312\Scripts\python.exe"

REM 1. 检查Python环境
echo [1/4] Python环境
if exist "%VENV_PYTHON%" (
    echo   ✅ 虚拟环境存在
    "%VENV_PYTHON%" --version
) else (
    echo   ❌ 虚拟环境不存在
)
echo.

REM 2. 检查运行中的进程
echo [2/4] 运行中的服务
tasklist | findstr /i "python.exe" | findstr /v "findstr" >nul 2>&1
if !errorlevel! equ 0 (
    echo   ⚠️  发现Python进程:
    tasklist | findstr /i "python.exe" | findstr /v "findstr"
) else (
    echo   ℹ️  没有运行中的Python进程
)
echo.

REM 3. 检查端口占用
echo [3/4] 端口状态
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo   ⚠️  端口 8000 已被占用
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
        echo      PID: %%a
    )
) else (
    echo   ✅ 端口 8000 空闲
)
echo.

REM 4. 测试后端连接
echo [4/4] 后端服务
curl -s http://localhost:8000/health >nul 2>&1
if !errorlevel! equ 0 (
    echo   ✅ 后端服务响应正常
    echo      http://localhost:8000/health
) else (
    echo   ❌ 后端服务无响应
    echo      可能未启动或启动失败
)
echo.

REM 总结
echo ============================================================
echo   快速操作
echo ============================================================
echo.
echo   • 启动系统: start.bat
echo   • 停止服务: stop.bat
echo   • 查看API:  http://localhost:8000/docs
echo.
echo ============================================================

pause
exit /b 0
