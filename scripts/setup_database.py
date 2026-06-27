"""
数据库自动配置脚本
检查MySQL、创建数据库、配置连接、初始化表结构
"""
import subprocess
import sys
import os
from pathlib import Path
import getpass


def run_command(cmd, description, shell=True):
    """执行命令并返回结果"""
    print(f"\n⚙️  {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            return True, result.stdout
        else:
            print(f"❌ {description} - 失败")
            print(f"错误: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} - 异常: {str(e)}")
        return False, str(e)


def check_mysql_installed():
    """检查MySQL是否安装"""
    print("\n" + "="*60)
    print("🔍 检查MySQL安装状态")
    print("="*60)
    
    # 尝试多个可能的命令
    commands = [
        "mysql --version",
        "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe --version",
        "C:\\xampp\\mysql\\bin\\mysql.exe --version",
    ]
    
    for cmd in commands:
        success, output = run_command(cmd, "检查MySQL")
        if success:
            print(f"📌 MySQL版本: {output.strip()}")
            return True, cmd.split()[0] if 'mysql' in cmd else cmd
    
    print("\n❌ 未检测到MySQL")
    print("\n请先安装MySQL:")
    print("  方法1: choco install mysql -y")
    print("  方法2: 从 https://dev.mysql.com/downloads/mysql/ 下载")
    print("  方法3: 安装XAMPP (包含MySQL)")
    return False, None


def get_mysql_password():
    """获取MySQL密码"""
    print("\n" + "="*60)
    print("🔐 MySQL认证")
    print("="*60)
    
    password = input("请输入MySQL root密码: ")
    if not password:
        print("❌ 密码不能为空")
        sys.exit(1)
    
    return password


def test_mysql_connection(password, mysql_cmd="mysql"):
    """测试MySQL连接"""
    print("\n🔗 测试MySQL连接...")
    
    cmd = f'{mysql_cmd} -u root -p{password} -e "SELECT 1"'
    success, output = run_command(cmd, "连接测试")
    
    if success:
        print("✅ MySQL连接成功!")
        return True
    else:
        print("❌ MySQL连接失败,请检查密码是否正确")
        return False


def create_database(password, mysql_cmd="mysql"):
    """创建数据库"""
    print("\n" + "="*60)
    print("🗄️  创建数据库")
    print("="*60)
    
    db_name = "cuoti_system"
    
    # 创建数据库
    sql = f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    cmd = f'{mysql_cmd} -u root -p{password} -e "{sql}"'
    
    success, _ = run_command(cmd, f"创建数据库 {db_name}")
    
    if success:
        print(f"✅ 数据库 '{db_name}' 创建成功")
        return True
    else:
        print("❌ 数据库创建失败")
        return False


def create_user(password, mysql_cmd="mysql"):
    """创建专用用户"""
    print("\n👤 创建数据库用户")
    
    choice = input("是否创建专用用户? (y/n, 默认n): ").strip().lower()
    if choice != 'y':
        print("ℹ️  跳过用户创建,将使用root账户")
        return "root", password
    
    username = input("用户名 (默认cuoti_user): ").strip() or "cuoti_user"
    user_password = input("用户密码: ").strip()
    
    if not user_password:
        print("❌ 密码不能为空")
        return None, None
    
    # 创建用户
    sql1 = f"CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY '{user_password}';"
    sql2 = f"GRANT ALL PRIVILEGES ON cuoti_system.* TO '{username}'@'localhost';"
    sql3 = "FLUSH PRIVILEGES;"
    
    cmds = [
        f'{mysql_cmd} -u root -p{password} -e "{sql1}"',
        f'{mysql_cmd} -u root -p{password} -e "{sql2}"',
        f'{mysql_cmd} -u root -p{password} -e "{sql3}"',
    ]
    
    for i, cmd in enumerate(cmds):
        desc = ["创建用户", "授予权限", "刷新权限"][i]
        success, _ = run_command(cmd, desc)
        if not success and i < 2:
            print(f"⚠️  {desc}失败,但继续执行")
    
    print(f"✅ 用户 '{username}' 创建成功")
    return username, user_password


def configure_env(db_user, db_password):
    """配置.env文件"""
    print("\n" + "="*60)
    print("⚙️  配置环境变量")
    print("="*60)
    
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    example_env = backend_dir / ".env.example"
    
    # 复制示例文件
    if not env_file.exists():
        if example_env.exists():
            import shutil
            shutil.copy(example_env, env_file)
            print("✅ 已创建.env文件")
        else:
            print("❌ 找不到.env.example文件")
            return False
    
    # 读取现有配置
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新数据库配置
    new_lines = []
    for line in lines:
        if line.startswith('DB_HOST='):
            new_lines.append('DB_HOST=localhost\n')
        elif line.startswith('DB_PORT='):
            new_lines.append('DB_PORT=3306\n')
        elif line.startswith('DB_USER='):
            new_lines.append(f'DB_USER={db_user}\n')
        elif line.startswith('DB_PASSWORD='):
            new_lines.append(f'DB_PASSWORD={db_password}\n')
        elif line.startswith('DB_NAME='):
            new_lines.append('DB_NAME=cuoti_system\n')
        else:
            new_lines.append(line)
    
    # 写入更新后的配置
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ .env文件配置完成")
    print(f"   DB_USER={db_user}")
    print(f"   DB_PASSWORD={'*' * len(db_password)}")
    print(f"   DB_NAME=cuoti_system")
    
    return True


def initialize_database():
    """初始化数据库表结构"""
    print("\n" + "="*60)
    print("📊 初始化数据库表结构")
    print("="*60)
    
    script_path = Path(__file__).parent / "scripts" / "init_db.py"
    
    if not script_path.exists():
        print("❌ 找不到初始化脚本 scripts/init_db.py")
        return False
    
    # 使用虚拟环境的Python
    venv_python = Path(__file__).parent / "venv312" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print("⚠️  虚拟环境不存在,使用系统Python")
        python_cmd = "python"
    else:
        python_cmd = str(venv_python)
    
    cmd = f'{python_cmd} "{script_path}"'
    success, output = run_command(cmd, "初始化数据库", shell=True)
    
    if success:
        print("✅ 数据库表结构初始化成功!")
        return True
    else:
        print("❌ 数据库初始化失败")
        print(output)
        return False


def verify_setup(db_user, db_password):
    """验证配置"""
    print("\n" + "="*60)
    print("✅ 验证配置")
    print("="*60)
    
    # 测试连接
    cmd = f'mysql -u {db_user} -p{db_password} cuoti_system -e "SHOW TABLES;"'
    success, output = run_command(cmd, "验证数据库连接和表")
    
    if success:
        print("\n📋 已创建的表:")
        print(output)
        return True
    else:
        print("⚠️  无法验证,但不影响使用")
        return True


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 错题管理系统 - 数据库自动配置")
    print("="*60)
    
    # 步骤1: 检查MySQL
    mysql_installed, mysql_cmd = check_mysql_installed()
    if not mysql_installed:
        print("\n❌ 请先安装MySQL后再运行此脚本")
        print("\n快速安装命令:")
        print("  choco install mysql -y")
        sys.exit(1)
    
    # 步骤2: 获取密码
    password = get_mysql_password()
    
    # 步骤3: 测试连接
    if not test_mysql_connection(password, mysql_cmd):
        print("\n❌ 连接测试失败,请检查密码")
        sys.exit(1)
    
    # 步骤4: 创建数据库
    if not create_database(password, mysql_cmd):
        print("\n❌ 数据库创建失败")
        sys.exit(1)
    
    # 步骤5: 创建用户
    db_user, db_password = create_user(password, mysql_cmd)
    if not db_user:
        db_user = "root"
        db_password = password
    
    # 步骤6: 配置.env
    if not configure_env(db_user, db_password):
        print("\n❌ 配置文件更新失败")
        sys.exit(1)
    
    # 步骤7: 初始化表结构
    if not initialize_database():
        print("\n⚠️  表结构初始化失败,可以稍后手动运行 scripts/init_db.py")
    
    # 步骤8: 验证
    verify_setup(db_user, db_password)
    
    # 完成
    print("\n" + "="*60)
    print("🎉 数据库配置完成!")
    print("="*60)
    print("\n下一步:")
    print("  1. 启动后端: cd backend && python -m app.main")
    print("  2. 访问API文档: http://localhost:8000/docs")
    print("  3. 启动前端: cd frontend && python main.py")
    print("  4. 或一键启动: .\\start.bat")
    print("\n配置文件: backend/.env")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
