@echo off
chcp 65001 >nul
REM MySQL快速安装脚本

echo.
echo ============================================================
echo 🚀 MySQL数据库快速安装
echo ============================================================
echo.

echo 请选择安装方式:
echo.
echo 1. 使用Chocolatey安装 (推荐,需要先安装choco)
echo 2. 手动下载安装
echo 3. 已安装MySQL,跳过此步骤
echo.

set /p choice="请输入选择 (1/2/3): "

if "%choice%"=="1" goto CHOCO_INSTALL
if "%choice%"=="2" goto MANUAL_INSTALL
if "%choice%"=="3" goto SKIP_INSTALL

echo 无效选择
pause
exit /b 1

:CHOCO_INSTALL
echo.
echo ============================================================
echo 使用Chocolatey安装MySQL...
echo ============================================================
echo.

where choco >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Chocolatey未安装
    echo.
    echo 请先安装Chocolatey:
    echo https://chocolatey.org/install
    pause
    exit /b 1
)

echo 正在安装MySQL...
choco install mysql -y

if %errorlevel% equ 0 (
    echo.
    echo ✅ MySQL安装成功!
    echo.
    echo 请记下root密码(安装过程中设置)
    echo.
    goto CONFIGURE
) else (
    echo ❌ 安装失败
    pause
    exit /b 1
)

:MANUAL_INSTALL
echo.
echo ============================================================
echo 手动安装MySQL
echo ============================================================
echo.
echo 请按以下步骤操作:
echo.
echo 1. 访问: https://dev.mysql.com/downloads/mysql/
echo 2. 下载 Windows (x86, 64-bit) MSI Installer
echo 3. 运行安装程序
echo 4. 选择 "Developer Default" 或 "Server only"
echo 5. 设置root密码(请记住!)
echo 6. 完成安装
echo.
echo 或者使用XAMPP (更简单):
echo 1. 访问: https://www.apachefriends.org/
echo 2. 下载并安装XAMPP
echo 3. 启动XAMPP Control Panel
echo 4. 点击MySQL的Start按钮
echo.

start https://dev.mysql.com/downloads/mysql/

echo.
set /p installed="安装完成后输入 y 继续: "
if /i "%installed%"=="y" goto CONFIGURE

pause
exit /b 0

:SKIP_INSTALL
echo.
echo ℹ️  跳过MySQL安装
goto CONFIGURE

:CONFIGURE
echo.
echo ============================================================
echo 配置数据库
echo ============================================================
echo.

cd /d "%~dp0"

echo 运行数据库配置脚本...
.\venv312\Scripts\python.exe setup_database.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ 数据库配置完成!
) else (
    echo.
    echo ❌ 配置失败,请查看错误信息
)

echo.
pause
