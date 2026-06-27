# 一键启动与停止脚本使用指南

## 📦 已创建的脚本

项目提供了三种启动方式,您可以根据喜好选择:

### 1. **start.bat** (推荐 - 最简单)
Windows批处理文件,双击即可运行

### 2. **start.ps1** (功能最全)
PowerShell脚本,提供更详细的控制和状态显示

### 3. **manage.py** (Python脚本)
跨平台Python脚本,适合集成到自动化流程

---

## 🚀 快速开始

### 方法1: 双击启动(最简单)

直接双击 `start.bat` 文件即可启动所有服务!

### 方法2: 命令行启动

**使用批处理文件:**
```bash
# 启动所有服务
start.bat

# 或指定命令
start.bat start
start.bat stop
start.bat restart
start.bat status
```

**使用PowerShell:**
```powershell
# 可能需要先允许执行脚本
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 启动服务
.\start.ps1

# 其他命令
.\start.ps1 stop
.\start.ps1 restart
.\start.ps1 status
```

**使用Python脚本:**
```bash
python manage.py start
python manage.py stop
python manage.py restart
python manage.py status
python manage.py backend   # 仅启动后端
python manage.py frontend  # 仅启动前端
```

---

## 📋 命令说明

### start - 启动所有服务
```bash
start.bat
# 或
start.bat start
```

**功能:**
- ✅ 自动检测Python环境
- ✅ 优先使用虚拟环境(venv312)
- ✅ 检查并创建.env配置文件
- ✅ 启动后端服务(FastAPI)
- ✅ 启动前端应用(PyQt6)
- ✅ 健康检查验证后端就绪

**输出示例:**
```
============================================================
🚀 启动后端服务...
============================================================

✅ 后端服务已启动
📍 API文档: http://localhost:8100/docs

⏳ 等待后端服务就绪...
✅ 后端服务就绪!

============================================================
🎨 启动前端应用...
============================================================

✅ 前端应用已启动

============================================================
🎉 所有服务已启动!
============================================================
```

---

### stop - 停止所有服务
```bash
start.bat stop
```

**功能:**
- 🔍 查找所有相关Python进程
- ⏹️ 安全终止后端和前端进程
- 🧹 清理PID文件

---

### restart - 重启所有服务
```bash
start.bat restart
```

**功能:**
- 先停止所有服务
- 等待2秒
- 重新启动所有服务

---

### status - 查看服务状态
```bash
start.bat status
```

**功能:**
- 📊 显示后端服务状态(通过端口检查)
- 🔍 列出运行中的Python进程
- 📝 显示访问地址信息

**输出示例:**
```
============================================================
📊 服务状态
============================================================

✅ 后端服务: 运行中 (端口 8100 已监听)

运行中的Python进程:
  python.exe    12345  Console  1  150 MB
  python.exe    12346  Console  1  120 MB

📝 访问地址:
  - API文档: http://localhost:8100/docs
  - 健康检查: http://localhost:8100/health
```

---

## 🔧 高级用法

### 仅启动后端
```bash
python manage.py backend
```

适用于:
- 只需要API服务
- 前端开发调试
- 第三方系统集成

### 仅启动前端
```bash
python manage.py frontend
```

适用于:
- 后端已在运行
- 单独测试前端界面

---

## 💡 使用技巧

### 1. 后台运行
使用 `start.bat` 启动后,可以安全关闭命令窗口,服务会继续在后台运行。

### 2. 查看日志
后端日志保存在: `backend/logs/`
- `app_YYYY-MM-DD.log` - 应用日志
- `error_YYYY-MM-DD.log` - 错误日志

### 3. 修改配置
编辑 `backend/.env` 文件修改配置:
```env
HOST=0.0.0.0
PORT=8100
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cuoti_system
```

### 4. 端口被占用
如果端口8100被占用,修改 `.env` 中的 `PORT` 配置。

---

## ❓ 常见问题

### Q1: 提示"找不到Python"
**解决:** 安装Python 3.11或3.12
```bash
py install 3.12
```

### Q2: 虚拟环境不存在
**解决:** 脚本会自动使用系统Python,或手动创建:
```bash
py -3.12 -m venv venv312
```

### Q3: 后端启动失败
**检查:**
1. 数据库是否运行
2. `.env` 配置是否正确
3. 端口8100是否被占用

**查看日志:**
```bash
type backend\logs\error_*.log
```

### Q4: 无法停止服务
**强制停止:**
```bash
# Windows
taskkill /F /IM python.exe

# PowerShell
Get-Process python | Stop-Process -Force
```

### Q5: PowerShell无法执行脚本
**解决:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🎯 推荐工作流程

### 日常开发
```bash
# 早上启动
start.bat

# 工作中...
# 访问 http://localhost:8100/docs 测试API
# 使用PyQt6界面操作

# 晚上停止
start.bat stop
```

### 调试模式
```bash
# 终端1 - 后端(可看到实时日志)
cd backend
python -m app.main

# 终端2 - 前端
cd frontend
python main.py
```

### 生产环境
```bash
# 使用nohup或systemd保持后台运行
nohup python manage.py start > /dev/null 2>&1 &
```

---

## 📊 脚本对比

| 特性 | start.bat | start.ps1 | manage.py |
|-----|-----------|-----------|-----------|
| 易用性 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| 功能完整性 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 跨平台 | ❌ | ❌ | ✅ |
| 彩色输出 | ❌ | ✅ | ✅ |
| 进程管理 | 基础 | 完整 | 完整 |
| 依赖 | 无 | PowerShell | Python |

**推荐:** 
- 日常使用: `start.bat`
- 需要详细控制: `start.ps1`
- 自动化脚本: `manage.py`

---

## 🔗 相关文件

- [start.bat](file://f:\CUOTI_Lingma\start.bat) - Windows批处理脚本
- [start.ps1](file://f:\CUOTI_Lingma\start.ps1) - PowerShell脚本
- [manage.py](file://f:\CUOTI_Lingma\manage.py) - Python管理脚本
- [INSTALL.md](file://f:\CUOTI_Lingma\INSTALL.md) - 安装指南
- [README.md](file://f:\CUOTI_Lingma\README.md) - 项目说明

---

**祝您使用愉快!** 🎉
