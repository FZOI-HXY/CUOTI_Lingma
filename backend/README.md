# 错题管理系统 - 后端服务

FastAPI后端服务,提供OCR处理和错题管理API。

## 功能模块

- **文件上传**: 安全的图片文件上传接口
- **OCR处理**: 集成PaddleOCR ppstructureV3和ppOCRv5
- **图像处理**: 版面分析、区域分割、遮罩处理
- **Markdown生成**: 结构化文档生成
- **错题管理**: CRUD操作和查询
- **系统监控**: 实时状态和统计

## API端点

### 文件上传
- `POST /api/v1/upload/image` - 上传图片
- `POST /api/v1/upload/batch` - 批量上传

### OCR处理
- `POST /api/v1/ocr/process` - 启动OCR处理
- `GET /api/v1/ocr/status/{task_id}` - 查询任务状态

### 错题管理
- `GET /api/v1/questions/` - 获取错题列表
- `GET /api/v1/questions/{id}` - 获取错题详情
- `POST /api/v1/questions/` - 创建错题
- `DELETE /api/v1/questions/{id}` - 删除错题

### 系统监控
- `GET /api/v1/system/status` - 系统状态
- `GET /api/v1/system/stats` - 统计数据
- `GET /api/v1/system/logs` - 处理日志

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env` 并修改配置。

## 启动服务

```bash
python -m app.main
```

或使用Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 开发模式

```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看交互式API文档。
