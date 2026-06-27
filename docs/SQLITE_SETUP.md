# SQLite数据库配置说明

## ✅ 已完成配置

系统已修改为使用**SQLite数据库**,无需安装MySQL!

### 优势:
- ✅ 无需安装MySQL服务器
- ✅ 单个文件,易于备份和迁移
- ✅ 自动创建,零配置
- ✅ 性能足够中小型应用
- ✅ SQLAlchemy原生支持

---

## 📁 数据库文件位置

数据库文件会自动创建在项目根目录:

```
f:\CUOTI_Lingma\cuoti_system.db
```

---

## 🚀 快速开始

### 1. 初始化数据库

```bash
cd f:\CUOTI_Lingma
.\venv312\Scripts\python.exe scripts/init_db.py
```

输出示例:
```
✅ SQLite数据库文件已创建: F:\CUOTI_Lingma\cuoti_system.db
Database initialization completed!
```

### 2. 启动系统

```bash
.\start.bat
```

或分别启动:
```bash
# 后端
cd backend
python -m app.main

# 前端
cd frontend
python main.py
```

---

## ⚙️ 配置说明

### 默认配置 (backend/.env)

```env
# SQLite配置(默认)
DB_FILE=cuoti_system.db
```

### 自定义数据库文件名

如果需要更改数据库文件名,编辑 `backend/.env`:

```env
DB_FILE=my_custom_database.db
```

---

## 📊 数据库管理

### 查看数据库文件

数据库是单个文件,可以直接复制备份:

```bash
# 备份
copy cuoti_system.db cuoti_system_backup.db

# 恢复
copy cuoti_system_backup.db cuoti_system.db
```

### 使用SQLite工具查看

可以使用以下工具查看和编辑SQLite数据库:

1. **DB Browser for SQLite** (推荐)
   - 下载: https://sqlitebrowser.org/
   - 图形界面,易于使用

2. **SQLite命令行**
   ```bash
   # Python内置
   .\venv312\Scripts\python.exe -m sqlite3 cuoti_system.db
   
   # 或使用sqlite3命令(如果安装)
   sqlite3 cuoti_system.db
   ```

3. **VS Code扩展**
   - 安装 "SQLite Viewer" 扩展
   - 直接点击.db文件查看

### 常用SQL查询

```sql
-- 查看所有表
.tables

-- 查看错题列表
SELECT * FROM questions;

-- 查看用户列表
SELECT * FROM users;

-- 统计错题数量
SELECT COUNT(*) FROM questions;

-- 删除所有数据(谨慎!)
DELETE FROM questions;
```

---

## 🔄 切换到MySQL(可选)

如果将来需要切换到MySQL:

### 1. 安装MySQL依赖

```bash
.\venv312\Scripts\python.exe -m pip install pymysql cryptography
```

### 2. 修改 backend/.env

```env
# 注释SQLite配置
# DB_FILE=cuoti_system.db

# 启用MySQL配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cuoti_system
```

### 3. 修改 backend/app/database.py

取消MySQL相关注释,注释SQLite配置。

### 4. 重新初始化

```bash
.\venv312\Scripts\python.exe scripts/init_db.py
```

---

## ❓ 常见问题

### Q1: 数据库文件在哪里?

A: 项目根目录下的 `cuoti_system.db`

### Q2: 如何备份数据库?

A: 直接复制 `cuoti_system.db` 文件即可

### Q3: 数据库太大怎么办?

A: 
- 定期清理旧数据
- 导出重要数据后重建数据库
- 考虑切换到MySQL

### Q4: 多用户可以同时访问吗?

A: 
- SQLite支持并发读
- 写操作会锁定数据库
- 对于高并发场景,建议切换到MySQL

### Q5: 性能如何?

A:
- 小规模(<10万条记录): 性能优秀
- 中等规模(10-50万条): 性能良好
- 大规模(>50万条): 建议切换到MySQL

---

## 📝 数据库表结构

系统包含以下表:

1. **users** - 用户信息
   - id, username, email, created_at

2. **questions** - 错题记录
   - id, user_id, original_image_path, processed_image_path
   - ocr_result_md, status, metadata, created_at

3. **processing_logs** - 处理日志
   - id, task_id, question_id, status, progress
   - error_message, created_at

4. **system_configs** - 系统配置
   - id, config_key, config_value, description

---

## 🎯 下一步

数据库配置完成后:

1. **初始化数据库**
   ```bash
   .\venv312\Scripts\python.exe scripts/init_db.py
   ```

2. **启动系统**
   ```bash
   .\start.bat
   ```

3. **访问API文档**
   - http://localhost:8000/docs

4. **开始使用!**

---

**无需安装MySQL,开箱即用!** 🎉
