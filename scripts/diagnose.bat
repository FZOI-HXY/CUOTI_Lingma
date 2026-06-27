@echo off
chcp 65001 >nul
REM 诊断脚本 - 检查系统配置

echo.
echo ============================================================
echo 🔍 系统诊断工具
echo ============================================================
echo.

cd /d "%~dp0.."

echo 📁 当前目录: %CD%
echo.

echo 1️⃣  检查关键文件...
echo.

if exist "backend\app\main.py" (
    echo    ✅ backend\app\main.py
) else (
    echo    ❌ backend\app\main.py [缺失]
)

if exist "frontend\main.py" (
    echo    ✅ frontend\main.py
) else (
    echo    ❌ frontend\main.py [缺失]
)

if exist "venv312\Scripts\python.exe" (
    echo    ✅ venv312\Scripts\python.exe
) else (
    echo    ❌ venv312\Scripts\python.exe [缺失]
)

if exist "backend\.env" (
    echo    ✅ backend\.env
) else (
    echo    ❌ backend\.env [缺失]
)

if exist "cuoti_system.db" (
    echo    ✅ cuoti_system.db
) else (
    echo    ⚠️  cuoti_system.db [未初始化]
)

echo.
echo 2️⃣  检查Python环境...
echo.

if exist "venv312\Scripts\python.exe" (
    venv312\Scripts\python.exe --version
) else (
    echo    ❌ Python虚拟环境不存在
)

echo.
echo 3️⃣  测试数据库连接...
echo.

if exist "venv312\Scripts\python.exe" (
    venv312\Scripts\python.exe -c "from backend.app.database import engine; print('✅ 数据库连接正常')" 2>nul
    if errorlevel 1 (
        echo    ❌ 数据库连接失败
    )
) else (
    echo    ⚠️  跳过(Python不存在)
)

echo.
echo 4️⃣  检查端口占用...
echo.

netstat -ano | findstr ":8100" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo    ⚠️  端口 8100 已被占用
    netstat -ano | findstr ":8100" | findstr "LISTENING"
) else (
    echo    ✅ 端口 8100 空闲
)

echo.
echo ============================================================
echo 📊 诊断完成
echo ============================================================
echo.

if exist "backend\app\main.py" if exist "frontend\main.py" if exist "venv312\Scripts\python.exe" (
    echo ✅ 所有必要文件都存在,可以启动系统
    echo.
    echo 启动命令:
    echo   .\start.bat
    echo.
) else (
    echo ❌ 缺少必要文件,请检查项目结构
    echo.
)

pause
