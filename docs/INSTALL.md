# 依赖安装说明

## ✅ 已完成安装

### 后端依赖 (FastAPI)
已安装以下核心包:
- fastapi - Web框架
- uvicorn - ASGI服务器
- sqlalchemy - ORM
- pymysql - MySQL驱动
- opencv-python - 图像处理
- pillow - 图片处理
- numpy - 数值计算
- loguru - 日志系统
- pydantic - 数据验证
- psutil - 系统监控
- 等其他依赖...

### 前端依赖 (PyQt6)
已安装:
- PyQt6 - GUI框架
- requests - HTTP客户端
- pillow - 图片处理

## ⚠️ PaddleOCR说明

由于您使用的是 **Python 3.14**,而PaddlePaddle目前仅支持 **Python 3.8-3.11**,因此PaddleOCR相关包暂时未安装。

### 解决方案

#### 方案1: 使用Mock模式(推荐用于测试)
系统已经实现了Mock模式,即使没有PaddleOCR也能运行:
- 可以测试上传、界面、数据库等功能
- OCR处理会返回模拟数据

直接启动即可使用基本功能。

#### 方案2: 创建Python 3.11环境(如需真实OCR)

如果您需要使用真实的PaddleOCR功能,建议:

**使用conda创建Python 3.11环境:**
```bash
conda create -n cuoti python=3.11
conda activate cuoti
cd backend
pip install -r requirements.txt
```

**或使用pyenv:**
```bash
pyenv install 3.11.9
pyenv local 3.11.9
pip install -r requirements.txt
```

然后在Python 3.11环境中取消requirements.txt中PaddleOCR相关包的注释。

## 🚀 启动系统

### 方式1: 分别启动

**终端1 - 启动后端:**
```bash
cd backend
python -m app.main
```

**终端2 - 启动前端:**
```bash
cd frontend
python main.py
```

### 方式2: 一键启动
```bash
python scripts/start_services.py
```

## 📝 配置数据库

在启动前,请确保:

1. **MySQL已安装并运行**

2. **创建数据库:**
```sql
CREATE DATABASE cuoti_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **配置.env文件:**
```bash
cd backend
copy .env.example .env
```

编辑 `.env` 文件,设置正确的数据库连接信息:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cuoti_system
```

4. **初始化数据库:**
```bash
python scripts/init_db.py
```

## 🔍 验证安装

### 检查后端
访问: http://localhost:8000/docs
应该能看到API文档页面

### 检查前端
运行 `python frontend/main.py`
应该能看到图形界面窗口

## ❓ 常见问题

### 1. 端口被占用
修改 `.env` 中的 `PORT` 配置

### 2. 数据库连接失败
- 检查MySQL服务是否启动
- 确认用户名密码正确
- 确认数据库已创建

### 3. PyQt6导入错误
重新安装: `pip install --force-reinstall PyQt6`

### 4. Mock模式提示
看到 "Using mock layout analysis" 是正常的,表示在没有PaddleOCR时使用模拟数据。

## 📊 当前状态

✅ 后端基础功能 - 已就绪
✅ 前端GUI - 已就绪  
✅ 数据库模型 - 已就绪
✅ 文件上传 - 已就绪
✅ 错题管理 - 已就绪
✅ 系统监控 - 已就绪
⚠️ PaddleOCR - Mock模式(需Python 3.11启用真实功能)

系统可以在Mock模式下完整测试除OCR识别外的所有功能!
