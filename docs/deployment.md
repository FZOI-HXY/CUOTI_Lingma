# 错题管理系统 - 部署指南

## 系统要求

- Python 3.9+
- MySQL 8.0+
- Windows/Linux/macOS

## 后端部署

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库

创建MySQL数据库:

```sql
CREATE DATABASE cuoti_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件,设置正确的数据库连接信息。

### 4. 启动后端服务

```bash
cd backend
python -m app.main
```

服务将在 `http://localhost:8000` 启动。

访问 `http://localhost:8000/docs` 查看API文档。

## 前端部署

### 1. 安装依赖

```bash
cd frontend
pip install -r requirements.txt
```

### 2. 启动前端应用

```bash
cd frontend
python main.py
```

## Docker部署(可选)

### 使用docker-compose

```bash
docker-compose up -d
```

## 常见问题

### 1. PaddleOCR模型下载失败

确保网络连接正常,首次运行会自动下载模型文件。

### 2. 数据库连接失败

检查MySQL服务是否启动,用户名密码是否正确。

### 3. 端口被占用

修改 `.env` 中的 `PORT` 配置或使用其他端口。

## 性能优化建议

1. 启用GPU加速: 设置 `OCR_USE_GPU=True`
2. 调整批处理大小
3. 使用Redis缓存任务状态
4. 配置Nginx反向代理

## 生产环境部署

1. 使用Gunicorn替代Uvicorn
2. 配置HTTPS
3. 启用身份验证
4. 设置防火墙规则
5. 配置日志轮转和监控
