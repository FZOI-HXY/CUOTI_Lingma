# MySQL数据库配置指南

## 📋 目录
1. [安装MySQL](#安装mysql)
2. [创建数据库](#创建数据库)
3. [配置连接](#配置连接)
4. [初始化表结构](#初始化表结构)
5. [常见问题](#常见问题)

---

## 🔧 安装MySQL

### 方法1: 使用Chocolatey(推荐)

```powershell
# 以管理员身份运行PowerShell
choco install mysql -y
```

### 方法2: 手动安装

1. 访问 MySQL官网下载: https://dev.mysql.com/downloads/mysql/
2. 选择 Windows (x86, 64-bit) MSI Installer
3. 下载并运行安装程序
4. 选择 "Developer Default" 或 "Server only"
5. 设置root密码(请记住这个密码!)
6. 完成安装

### 方法3: 使用XAMPP(包含MySQL)

1. 下载XAMPP: https://www.apachefriends.org/
2. 安装时勾选MySQL
3. 启动XAMPP Control Panel
4. 点击MySQL的Start按钮

---

## 🗄️ 创建数据库

### 步骤1: 连接到MySQL

**使用命令行:**
```bash
mysql -u root -p
# 输入密码
```

**或使用MySQL Workbench:**
1. 打开MySQL Workbench
2. 点击 "+" 添加新连接
3. 主机: localhost, 端口: 3306
4. 用户名: root
5. 点击测试连接,然后确定

### 步骤2: 创建数据库

在MySQL命令行中执行:

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS cuoti_system 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 查看数据库
SHOW DATABASES;

-- 使用数据库
USE cuoti_system;
```

### 步骤3: 创建专用用户(可选但推荐)

```sql
-- 创建用户
CREATE USER IF NOT EXISTS 'cuoti_user'@'localhost' IDENTIFIED BY 'your_password';

-- 授予权限
GRANT ALL PRIVILEGES ON cuoti_system.* TO 'cuoti_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 查看用户
SELECT user, host FROM mysql.user;
```

---

## ⚙️ 配置连接

### 编辑 backend/.env 文件

复制 `.env.example` 为 `.env`:

```bash
cd backend
copy .env.example .env
```

编辑 `.env` 文件:

```env
# 服务器配置
HOST=0.0.0.0
PORT=8100
DEBUG=True

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root              # 如果使用专用用户,改为 cuoti_user
DB_PASSWORD=your_password # 修改为您的MySQL密码
DB_NAME=cuoti_system

# JWT配置
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 文件存储配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# OCR配置
OCR_MOCK_MODE=False     # 如果有PaddleOCR设为False,否则设为True
```

**重要:**
- `DB_PASSWORD`: 必须修改为您的MySQL root密码
- `DB_USER`: 如果创建了专用用户,使用 `cuoti_user`
- `OCR_MOCK_MODE`: 
  - `True` - 使用模拟数据(不需要PaddleOCR)
  - `False` - 使用真实PaddleOCR

---

## 📊 初始化表结构

### 方法1: 使用初始化脚本(推荐)

```bash
cd f:\CUOTI_Lingma
.\venv312\Scripts\python.exe scripts/init_db.py
```

这个脚本会:
- ✅ 检查数据库连接
- ✅ 创建所有表结构
- ✅ 创建默认管理员账户
- ✅ 验证表是否创建成功

### 方法2: 使用Alembic迁移

```bash
cd backend

# 初始化迁移环境(首次)
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 方法3: 手动执行SQL

查看 `backend/app/models.py` 中的表结构,手动创建表。

---

## ✅ 验证配置

### 测试数据库连接

```bash
cd f:\CUOTI_Lingma
.\venv312\Scripts\python.exe -c "
from backend.app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ 数据库连接成功!')
except Exception as e:
    print(f'❌ 连接失败: {e}')
"
```

### 检查表是否创建

```sql
USE cuoti_system;
SHOW TABLES;
```

应该看到:
- users
- questions
- processing_logs
- system_configs

---

## ❓ 常见问题

### Q1: 无法连接到MySQL

**检查:**
1. MySQL服务是否运行
   ```powershell
   # 检查服务状态
   Get-Service MySQL* 
   
   # 启动服务
   Start-Service MySQL80
   ```

2. 端口是否正确(默认3306)
   ```bash
   netstat -ano | findstr :3306
   ```

3. 防火墙是否阻止连接

### Q2: Access denied错误

**解决:**
```sql
-- 重置root密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

### Q3: 字符集问题

确保数据库使用utf8mb4:
```sql
ALTER DATABASE cuoti_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Q4: 忘记MySQL密码

**Windows重置密码:**
1. 停止MySQL服务
   ```powershell
   Stop-Service MySQL80
   ```

2. 以跳过授权表方式启动
   ```bash
   mysqld --skip-grant-tables
   ```

3. 新开命令行窗口,无密码登录
   ```bash
   mysql -u root
   ```

4. 重置密码
   ```sql
   FLUSH PRIVILEGES;
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
   EXIT;
   ```

5. 重启MySQL服务
   ```powershell
   Start-Service MySQL80
   ```

### Q5: 表创建失败

**检查:**
1. 数据库是否存在
2. 用户是否有权限
3. 查看错误日志: `backend/logs/error_*.log`

---

## 🚀 快速开始(一键配置)

如果您已经安装了MySQL,可以运行自动化配置脚本:

```bash
cd f:\CUOTI_Lingma
.\venv312\Scripts\python.exe setup_database.py
```

这个脚本会:
1. 检查MySQL是否安装
2. 提示输入root密码
3. 自动创建数据库
4. 自动创建用户
5. 配置.env文件
6. 初始化表结构

---

## 📝 下一步

配置完数据库后:

1. **启动后端服务**
   ```bash
   cd backend
   python -m app.main
   ```

2. **访问API文档**
   - http://localhost:8100/docs

3. **启动前端应用**
   ```bash
   cd frontend
   python main.py
   ```

4. **或使用一键启动**
   ```bash
   cd f:\CUOTI_Lingma
   .\start.bat
   ```

---

**祝您配置顺利!** 🎉
