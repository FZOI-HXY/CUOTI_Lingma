@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM ============================================================
REM Cuoti Management System - One-click Startup Script
REM Use absolute paths to avoid path issues
REM ============================================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM 设置项目路径(使用绝对路径)
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "VENV_PYTHON=%PROJECT_ROOT%\venv312\Scripts\python.exe"
set "ENV_FILE=%BACKEND_DIR%\.env"

title 错题管理系统启动器

echo.
echo ============================================================
echo   🚀 错题管理系统 - 启动程序
echo ============================================================
echo.
echo   项目目录: %PROJECT_ROOT%
echo.

REM ============================================================
REM 步骤1: 检查必要文件
REM ============================================================
echo [1/5] 检查系统文件...

if not exist "%VENV_PYTHON%" (
    echo.
    echo   ❌ 错误: Python虚拟环境不存在
    echo      路径: %VENV_PYTHON%
    echo.
    echo   请先创建虚拟环境并安装依赖
    pause
    exit /b 1
)
echo   ✅ Python环境正常

if not exist "%BACKEND_DIR%\app\main.py" (
    echo.
    echo   ❌ 错误: 后端主程序不存在
    echo      路径: %BACKEND_DIR%\app\main.py
    pause
    exit /b 1
)
echo   ✅ 后端程序存在

if not exist "%FRONTEND_DIR%\main.py" (
    echo.
    echo   ❌ 错误: 前端主程序不存在
    echo      路径: %FRONTEND_DIR%\main.py
    pause
    exit /b 1
)
echo   ✅ 前端程序存在

if not exist "%ENV_FILE%" (
    echo   ⚠️  .env文件不存在,从示例复制...
    if exist "%BACKEND_DIR%\.env.example" (
        copy "%BACKEND_DIR%\.env.example" "%ENV_FILE%" >nul
        echo   ✅ 已创建.env文件
    ) else (
        echo   ❌ 错误: 找不到.env.example
        pause
        exit /b 1
    )
) else (
    echo   ✅ 配置文件存在
)

if not exist "%PROJECT_ROOT%\cuoti_system.db" (
    echo   ⚠️  数据库未初始化,正在初始化...
    "%VENV_PYTHON%" "%PROJECT_ROOT%\scripts\init_db.py"
    if errorlevel 1 (
        echo   ❌ 数据库初始化失败
        pause
        exit /b 1
    )
    echo   ✅ 数据库初始化完成
) else (
    echo   ✅ 数据库文件存在
)

echo.

REM ============================================================
REM 步骤2: 检查端口占用
REM ============================================================
echo [2/5] 检查端口状态...

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo   ⚠️  端口 8000 已被占用
    echo.
    echo   可能的原因:
    echo     - 之前启动的服务未关闭
    echo     - 其他程序使用了8000端口
    echo.
    
    set /p choice="是否停止占用端口的进程? (y/n): "
    if /i "!choice!"=="y" (
        echo.
        echo   正在查找占用进程...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
            set "PID=%%a"
        )
        
        if defined PID (
            echo   发现进程 PID: !PID!
            taskkill /F /PID !PID! >nul 2>&1
            if !errorlevel! equ 0 (
                echo   ✅ 已停止进程
            ) else (
                echo   ⚠️  需要管理员权限,请手动停止进程 !PID!
                pause
            )
        )
        
        REM 再次检查
        netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
        if !errorlevel! equ 0 (
            echo   ❌ 端口仍被占用,无法启动
            pause
            exit /b 1
        )
    ) else (
        echo   ❌ 用户取消,退出启动
        pause
        exit /b 1
    )
)
echo   ✅ 端口 8000 可用

echo.

REM ============================================================
REM 步骤3: 测试数据库连接
REM ============================================================
echo [3/5] 测试数据库连接...

"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, r'%BACKEND_DIR%'); from app.database import engine; print('OK')" >nul 2>&1
if !errorlevel! neq 0 (
    echo   ❌ 数据库连接失败
    echo.
    echo   请运行以下命令重新初始化:
    echo     %VENV_PYTHON% scripts\init_db.py
    pause
    exit /b 1
)
echo   ✅ 数据库连接正常

echo.

REM ============================================================
REM 步骤4: 启动后端服务
REM ============================================================
echo [4/5] 启动后端服务...
echo.

start "后端服务 - FastAPI" cmd /k "cd /d "%BACKEND_DIR%" && title 后端服务 && color 0A && echo ============================================================ && echo   后端服务启动中... && echo ============================================================ && echo. && "%VENV_PYTHON%" -m app.main"

echo   ✅ 后端服务已启动
echo   📍 API文档: http://localhost:8000/docs
echo   💡 提示: 后端窗口会显示实时日志

echo.

REM 等待后端启动
echo   等待后端就绪...
timeout /t 3 /nobreak >nul

REM 健康检查
echo   | set /p dummy="   检查服务状态..."
for /l %%i in (1,1,5) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ 后端服务就绪!
        goto backend_ready
    )
    timeout /t 1 /nobreak >nul
)
echo ⚠️  后端可能未完全启动,但继续启动前端

:backend_ready

echo.

REM ============================================================
REM 步骤5: 启动前端应用
REM ============================================================
echo [5/5] 启动前端应用...
echo.

start "前端应用 - PyQt6" cmd /k "cd /d "%FRONTEND_DIR%" && title 前端应用 && color 0B && echo ============================================================ && echo   前端应用启动中... && echo ============================================================ && echo. && "%VENV_PYTHON%" main.py"

echo   ✅ 前端应用已启动
echo   💡 提示: PyQt6界面将自动打开

echo.
echo ============================================================
echo   🎉 系统启动成功!
echo ============================================================
echo.
echo   📌 访问地址:
echo      • API文档:  http://localhost:8000/docs
echo      • 健康检查: http://localhost:8000/health
echo.
echo   📌 服务窗口:
echo      • 后端服务 - 查看API日志
echo      • 前端应用 - 图形化操作界面
echo.
echo   📌 停止服务:
echo      • 关闭对应的窗口即可
echo      • 或运行: stop_all.bat
echo.
echo   💡 提示:
echo      • 不要关闭此窗口(它只是启动器)
echo      • 可以最小化,服务会继续运行
echo.
echo ============================================================

REM 保持窗口打开,显示帮助信息
echo.
echo   按任意键关闭此启动器窗口(不影响服务)...
pause >nul

exit /b 0
