# 错题管理系统

一个基于PyQt6 + FastAPI + PaddleOCR的智能错题管理程序服务端系统。

## 功能特性

- ✅ 图片上传和安全传输
- ✅ PaddleOCR ppstructureV3版面分析
- ✅ 图片区域分割和遮罩处理
- ✅ ppOCRv5文字识别
- ✅ 结构化Markdown文档生成
- ✅ PyQt6图形化配置界面
- ✅ 服务端图形化管理界面
- ✅ MySQL数据持久化
- ✅ 实时系统监控
- ✅ 完整的日志系统

## 技术栈

### 后端
- **Web框架**: FastAPI + Uvicorn
- **数据库**: MySQL + SQLAlchemy
- **OCR引擎**: PaddlePaddle + PaddleX (ppstructureV3 + ppOCRv5)
- **图像处理**: OpenCV, Pillow
- **日志**: Loguru

### 前端
- **GUI框架**: PyQt6
- **HTTP客户端**: Requests

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd CUOTI_Lingma
```

### 2. 后端部署

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件,设置数据库连接

# 启动服务
python -m app.main
```

### 3. 前端部署

```bash
# 安装依赖
cd frontend
pip install -r requirements.txt

# 启动应用
python main.py
```

## 项目结构

```
CUOTI_Lingma/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── routers/     # API路由
│   │   ├── services/    # 业务逻辑
│   │   ├── models.py    # 数据模型
│   │   ├── schemas.py   # Pydantic schema
│   │   └── main.py      # 应用入口
│   └── requirements.txt
├── frontend/            # PyQt6客户端
│   ├── ui/             # 界面组件
│   ├── api/            # API客户端
│   ├── config/         # 配置管理
│   └── main.py         # 应用入口
├── docs/               # 文档
└── README.md
```

## API文档

启动后端后访问: `http://localhost:8000/docs`

## 配置说明

详见 [配置文档](docs/configuration.md)

## 使用手册

详见 [用户手册](docs/user_manual.md)

## 开发计划

- [ ] 支持PDF文件处理
- [ ] AI错题分类推荐
- [ ] 多用户协作功能
- [ ] 云端同步备份
- [ ] 移动端APP

## 许可证

MIT License

## 联系方式

如有问题,请提交Issue或联系开发者。
