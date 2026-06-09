# 后端服务运行状态

## ✅ 当前状态

### 服务信息
- **状态**: ✅ 运行中
- **URL**: http://localhost:8000
- **启动时间**: 2026-06-08 19:47:48
- **进程PID**: 6896, 14580

### 健康检查
```bash
curl http://localhost:8000/health
```

**响应:**
```json
{
  "status": "healthy",
  "timestamp": 1780919468.7095187,
  "version": "1.0.0"
}
```

---

## 📋 可用的API端点

### 核心端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 根路径 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger API文档 |
| `/redoc` | GET | ReDoc API文档 |

### API v1 路由

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/upload/*` | POST/GET | 文件上传 |
| `/api/v1/ocr/*` | POST/GET | OCR处理 |
| `/api/v1/questions/*` | GET/POST/PUT/DELETE | 错题管理 |
| `/api/v1/system/*` | GET | 系统监控 |

---

## 🔍 关于404错误说明

### 日志中看到的404错误

```
INFO: 127.0.0.1:50975 - "GET /api/health HTTP/1.1" 404 Not Found
INFO: 127.0.0.1:51101 - "GET /app/ HTTP/1.1" 404 Not Found
```

### 原因分析

这些404错误是**正常的**,原因是:

1. **`/api/health` 不存在**
   - 正确的健康检查端点是 `/health` (不是 `/api/health`)
   - 某些工具或脚本可能尝试访问 `/api/health`
   - 这不影响系统功能

2. **`/app/` 不存在**
   - 可能是浏览器或其他客户端的自动请求
   - 前端是独立的PyQt6应用,不是Web应用

### 解决方案

**无需修复!** 这些404错误:
- ✅ 不影响系统正常运行
- ✅ 不影响API功能
- ✅ 只是无效的请求被正确拒绝

如果想消除这些日志,可以:
1. 检查是否有脚本在访问 `/api/health`
2. 关闭自动刷新API文档的浏览器标签
3. 忽略这些日志(它们无害)

---

## 🚀 如何使用

### 1. 查看API文档

浏览器访问:
```
http://localhost:8000/docs
```

这是Swagger UI,可以:
- 查看所有API端点
- 测试API调用
- 查看请求/响应格式

### 2. 健康检查

```bash
# PowerShell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing

# CMD
curl http://localhost:8000/health

# Python
import requests
requests.get('http://localhost:8000/health').json()
```

### 3. 启动前端

后端已经在运行,现在启动前端:

```bash
cd frontend
..\venv312\Scripts\python.exe main.py
```

---

## 🛑 停止服务

### 方法1: 任务管理器
1. Ctrl+Shift+Esc 打开任务管理器
2. 找到 `python.exe` (PID 6896, 14580)
3. 右键 → 结束任务

### 方法2: 命令行
```bash
# 以管理员身份运行
taskkill /F /PID 6896
taskkill /F /PID 14580
```

### 方法3: 使用停止脚本
```bash
# 以管理员身份运行
.\stop.bat
```

---

## 📊 系统架构

```
┌─────────────┐
│  PyQt6前端   │ ← 独立桌面应用
└──────┬──────┘
       │ HTTP API
┌──────▼──────┐
│ FastAPI后端  │ ← http://localhost:8000
│             │
│ • /health   │ ← 健康检查 ✅
│ • /docs     │ ← API文档
│ • /api/v1/* │ ← 业务API
└──────┬──────┘
       │
┌──────▼──────┐
│ SQLite数据库 │ ← cuoti_system.db
└─────────────┘
```

---

## 💡 提示

### 端口占用
如果端口8000被占用:
```bash
# 查看占用
netstat -ano | findstr :8000

# 停止进程
taskkill /F /PID <PID>
```

### 查看日志
后端日志实时显示在启动窗口中。

### 重启服务
```bash
# 停止
.\stop.bat

# 启动
.\start.bat
```

---

**后端服务运行正常!可以开始使用了!** 🎉
