"""
Python 3.11/3.12 环境自动设置脚本
自动创建虚拟环境并安装PaddlePaddle
"""
import subprocess
import sys
import os


def run_command(cmd, description):
    """执行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"📌 {description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ 命令执行失败")
        return False
    else:
        print(f"✅ 成功")
        return True


def check_python_version(python_cmd):
    """检查Python版本"""
    try:
        result = subprocess.run(
            f"{python_cmd} --version",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return None


def main():
    print("\n" + "="*60)
    print("🚀 Python 3.11/3.12 环境自动设置工具")
    print("="*60)
    
    # 步骤1: 检查Python 3.11或3.12是否可用
    print("\n🔍 检查可用的Python版本...")
    
    python_cmd = None
    for version in ['3.11', '3.12']:
        py_cmd = f"py -{version}"
        ver_str = check_python_version(py_cmd)
        if ver_str:
            print(f"✅ 找到 {ver_str}")
            python_cmd = py_cmd
            break
    
    if not python_cmd:
        print("❌ 未找到Python 3.11或3.12")
        print("\n请先运行: py install 3.11")
        input("\n按回车键退出...")
        return
    
    # 步骤2: 创建虚拟环境
    venv_name = "venv_py311" if "3.11" in python_cmd else "venv_py312"
    
    if not run_command(
        f"{python_cmd} -m venv {venv_name}",
        f"创建虚拟环境 ({venv_name})"
    ):
        print("❌ 虚拟环境创建失败")
        input("\n按回车键退出...")
        return
    
    # 步骤3: 激活虚拟环境并安装依赖
    activate_script = f"{venv_name}\\Scripts\\activate.bat"
    pip_cmd = f"{venv_name}\\Scripts\\pip.exe"
    python_in_venv = f"{venv_name}\\Scripts\\python.exe"
    
    print(f"\n📦 开始安装依赖...")
    
    # 升级pip
    run_command(
        f"{pip_cmd} install --upgrade pip",
        "升级pip"
    )
    
    # 安装后端依赖
    print("\n📥 安装后端依赖...")
    
    # 先安装基础包
    base_packages = [
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "pymysql",
        "opencv-python",
        "pillow",
        "numpy",
        "loguru",
        "pydantic",
        "psutil",
        "python-dotenv",
        "alembic",
        "cryptography",
        "python-multipart",
        "aiofiles",
        "python-jose[cryptography]",
        "passlib[bcrypt]"
    ]
    
    packages_str = " ".join(base_packages)
    run_command(
        f"{pip_cmd} install {packages_str}",
        "安装基础依赖包"
    )
    
    # 安装PaddlePaddle
    print("\n🧠 安装PaddlePaddle...")
    paddle_installed = run_command(
        f"{pip_cmd} install paddlepaddle",
        "安装PaddlePaddle (最新版本)"
    )
    
    if not paddle_installed:
        print("\n⚠️ 尝试安装CPU版本...")
        run_command(
            f"{pip_cmd} install paddlepaddle-cpu",
            "安装PaddlePaddle-CPU"
        )
    
    # 安装PaddleOCR
    print("\n📝 安装PaddleOCR...")
    run_command(
        f"{pip_cmd} install paddleocr paddlex",
        "安装PaddleOCR和PaddleX"
    )
    
    # 安装前端依赖
    print("\n🎨 安装前端依赖...")
    run_command(
        f"{pip_cmd} install PyQt6 requests",
        "安装PyQt6和requests"
    )
    
    # 验证安装
    print("\n🔍 验证安装...")
    
    # 检查PaddlePaddle
    result = subprocess.run(
        f"{python_in_venv} -c \"import paddle; print('PaddlePaddle version:', paddle.__version__)\"",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"✅ {result.stdout.strip()}")
    else:
        print("❌ PaddlePaddle导入失败")
    
    # 检查PyQt6
    result = subprocess.run(
        f"{python_in_venv} -c \"import PyQt6; print('PyQt6 installed successfully')\"",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"✅ {result.stdout.strip()}")
    else:
        print("❌ PyQt6导入失败")
    
    # 完成
    print("\n" + "="*60)
    print("🎉 环境设置完成!")
    print("="*60)
    print(f"\n虚拟环境: {venv_name}")
    print(f"\n激活环境:")
    print(f"  PowerShell: .\\{venv_name}\\Scripts\\Activate.ps1")
    print(f"  CMD:        .\\{venv_name}\\Scripts\\activate.bat")
    print(f"\n启动后端:")
    print(f"  cd backend")
    print(f"  python -m app.main")
    print(f"\n启动前端:")
    print(f"  cd frontend")
    print(f"  python main.py")
    print("\n" + "="*60)
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
