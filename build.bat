@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ============================================
echo    错题管理系统 - 构建安装包
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"
set "VENV=%PROJECT_DIR%venv312\Scripts"
set "PYINSTALLER=%VENV%\pyinstaller.exe"
set "PYTHON=%VENV%\python.exe"
set "DIST_DIR=%PROJECT_DIR%dist"
set "MODEL_DIR=E:\Program Files\PP_Models\official_models"

REM ── Step 1: 检查环境 ──
echo [Step 1/5] 检查构建环境...

if not exist "%PYTHON%" (
    echo [ERROR] 未找到 Python: %PYTHON%
    echo         请先运行 setup_env.py 创建虚拟环境
    pause
    exit /b 1
)

if not exist "%PYINSTALLER%" (
    echo [WARN] 未找到 PyInstaller，正在安装...
    "%VENV%\pip.exe" install pyinstaller --quiet
)

echo [OK] 环境检查通过
echo.

REM ── Step 2: 清理旧构建 ──
echo [Step 2/5] 清理旧构建文件...

if exist "%DIST_DIR%" (
    rmdir /s /q "%DIST_DIR%"
    echo [OK] 已清理 %DIST_DIR%
)

if exist "%PROJECT_DIR%build" (
    rmdir /s /q "%PROJECT_DIR%build"
    echo [OK] 已清理 build 目录
)
echo.

REM ── Step 3: 构建后端 ──
echo [Step 3/5] 构建后端 (FastAPI)...
echo.

cd /d "%PROJECT_DIR%backend"
"%PYINSTALLER%" "%PROJECT_DIR%build_backend.spec" --distpath "%DIST_DIR%" --workpath "%PROJECT_DIR%build\backend" --noconfirm

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] 后端构建失败!
    pause
    exit /b 1
)

echo.
echo [OK] 后端构建完成
echo.

REM ── Step 4: 构建前端 ──
echo [Step 4/5] 构建前端 (PyQt6)...
echo.

cd /d "%PROJECT_DIR%frontend"
"%PYINSTALLER%" "%PROJECT_DIR%build_frontend.spec" --distpath "%DIST_DIR%" --workpath "%PROJECT_DIR%build\frontend" --noconfirm

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] 前端构建失败!
    pause
    exit /b 1
)

echo.
echo [OK] 前端构建完成
echo.

REM ── Step 5: 组装发布包 ──
echo [Step 5/5] 组装发布包...

set "RELEASE_DIR=%DIST_DIR%\CuotiSystem"

REM 复制后端
if not exist "%RELEASE_DIR%\backend" mkdir "%RELEASE_DIR%\backend"
xcopy /s /e /y "%DIST_DIR%\cuoti_backend\*" "%RELEASE_DIR%\backend\" >nul 2>&1

REM 复制前端
if not exist "%RELEASE_DIR%\frontend" mkdir "%RELEASE_DIR%\frontend"
xcopy /s /e /y "%DIST_DIR%\cuoti_frontend\*" "%RELEASE_DIR%\frontend\" >nul 2>&1

REM 复制启动脚本
copy /y "%PROJECT_DIR%start.bat" "%RELEASE_DIR%\" >nul 2>&1

REM 复制模型目录（PP-StructureV3 + VL GGUF 模型）
if exist "%MODEL_DIR%" (
    echo.
    echo 正在复制模型文件（请耐心等待）...
    if not exist "%RELEASE_DIR%\models" mkdir "%RELEASE_DIR%\models"
    xcopy /s /e /y "%MODEL_DIR%\*" "%RELEASE_DIR%\models\" >nul 2>&1
    echo [OK] 模型文件已复制
)

REM 复制 llama.cpp 工具（VL 增强模式推理引擎）
set "LLAMA_SRC=%PROJECT_DIR%tools\llama-cpp"
if exist "%LLAMA_SRC%\llama-server.exe" (
    echo.
    echo 正在复制 llama.cpp 工具...
    if not exist "%RELEASE_DIR%\tools\llama-cpp" mkdir "%RELEASE_DIR%\tools\llama-cpp"
    xcopy /s /e /y "%LLAMA_SRC%\*" "%RELEASE_DIR%\tools\llama-cpp\" >nul 2>&1
    echo [OK] llama.cpp 工具已复制
) else (
    echo.
    echo [WARN] 未找到 llama.cpp 工具，VL 增强模式将不可用
    echo        路径: %LLAMA_SRC%
)

REM 创建空目录
if not exist "%RELEASE_DIR%\uploads" mkdir "%RELEASE_DIR%\uploads"
if not exist "%RELEASE_DIR%\processed" mkdir "%RELEASE_DIR%\processed"
if not exist "%RELEASE_DIR%\logs" mkdir "%RELEASE_DIR%\logs"

echo.
echo ============================================
echo   构建完成!
echo.
echo   发布目录: %RELEASE_DIR%
echo   后端:     %RELEASE_DIR%\backend\cuoti_backend.exe
echo   前端:     %RELEASE_DIR%\frontend\cuoti_frontend.exe
echo.
echo   下一步: 用 Inno Setup 打开 installer.iss
echo           编译生成 .exe 安装包
echo ============================================
echo.

pause
