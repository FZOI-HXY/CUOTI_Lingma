# 数据库配置快速指南

## 🚀 三步完成数据库配置

### 步骤1: 安装MySQL (如果还没有)

**选项A: 使用Chocolatey(最简单)**
```powershell
# 以管理员身份运行PowerShell
choco install mysql -y
```

**选项B: 手动安装**
1. 访问: https://dev.mysql.com/downloads/mysql/
2. 下载 Windows MSI Installer
3. 安装时记住设置的root密码

**选项C: 使用XAMPP(包含MySQL,更简单)**
1. 访问: https://www.apachefriends.org/
2. 安装XAMPP
3. 启动XAMPP Control Panel,点击MySQL的Start

---

### 步骤2: 运行自动配置脚本

```bash
cd f:\CUOTI_Lingma
.\venv312\Scripts\python.exe setup_database.py
```

脚本会自动:
- ✅ 检查MySQL是否安装
- ✅ 提示输入MySQL root密码
- ✅ 创建数据库 `cuoti_system`
- ✅ 创建专用用户(可选)
- ✅ 配置 backend/.env 文件
- ✅ 初始化表结构

---

### 步骤3: 验证配置

```bash
# 测试连接
.\venv312\Scripts\python.exe -c "
from backend.app.database import engine
print('✅ 数据库配置成功!' if engine else '❌ 失败')
"
```

---

## 📝 手动配置(如果自动脚本失败)

### 1. 创建数据库

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE IF NOT EXISTS cuoti_system 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 退出
EXIT;
```

### 2. 配置 backend/.env

编辑 `backend/.env` 文件:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=cuoti_system
```

### 3. 初始化表结构

```bash
cd f:\CUOTI_Lingma
.\venv312\Scripts\python.exe scripts/init_db.py
```

---

## ❓ 常见问题

### MySQL未安装?
运行: `install_mysql.bat`

### 忘记MySQL密码?
参考 [DATABASE_SETUP.md](DATABASE_SETUP.md) 中的"忘记密码"部分

### 连接失败?
1. 检查MySQL服务是否运行: `Get-Service MySQL*`
2. 检查端口: `netstat -ano | findstr :3306`
3. 检查.env配置是否正确

---

## 🎯 下一步

配置完成后:

```bash
# 一键启动系统
.\start.bat

# 或分别启动
cd backend && python -m app.main   # 后端
cd frontend && python main.py      # 前端
```

访问: http://localhost:8000/docs

---

**详细文档**: [DATABASE_SETUP.md](DATABASE_SETUP.md)
