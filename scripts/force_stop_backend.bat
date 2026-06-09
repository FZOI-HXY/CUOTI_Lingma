@echo off
chcp 65001 >nul 2>&1

REM ============================================================
REM 强制停止后端服务 - 需要管理员权限
REM ============================================================

echo.
echo ============================================================
echo   🛑 强制停止后端服务 (PID 14580)
echo ============================================================
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 需要管理员权限!
    echo.
    echo 请右键点击此文件 → "以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo ✅ 已获得管理员权限
echo.

REM 方法1: 使用taskkill强制停止
echo [方法1] 尝试 taskkill 强制停止...
taskkill /F /PID 14580
if %errorlevel% equ 0 (
    echo ✅ 成功停止进程 14580
    goto CHECK_PORT
) else (
    echo ⚠️  taskkill 失败,尝试其他方法...
)

echo.

REM 方法2: 使用wmic停止
echo [方法2] 尝试 wmic 停止...
wmic process where "ProcessId=14580" delete
if %errorlevel% equ 0 (
    echo ✅ 成功停止进程 14580
    goto CHECK_PORT
) else (
    echo ⚠️  wmic 也失败了
)

echo.

REM 方法3: 查找并停止所有监听8000端口的进程
echo [方法3] 查找占用端口8000的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    set PID=%%a
    echo   发现进程 PID: !PID!
    
    echo   正在停止 PID !PID! ...
    taskkill /F /PID !PID!
    
    if !errorlevel! equ 0 (
        echo   ✅ 成功停止 PID !PID!
    ) else (
        echo   ❌ 无法停止 PID !PID!
    )
)

:CHECK_PORT
echo.
echo 检查端口8000状态...
timeout /t 2 /nobreak >nul

netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口8000仍被占用
    echo.
    echo 建议操作:
    echo   1. 重启计算机
    echo   2. 或者更换后端端口(修改 backend\.env 中的 PORT)
) else (
    echo ✅ 端口8000已释放
)

echo.
echo ============================================================
echo   完成!
echo ============================================================
echo.
pause
exit /b 0
