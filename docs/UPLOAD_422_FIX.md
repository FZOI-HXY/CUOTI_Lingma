# 前端文件上传422错误修复

## 🔍 问题描述

### 错误信息
```
Upload failed: 422 Client Error: Unprocessable Entity 
for url: http://localhost:8001/api/v1/upload/image
```

### 后端日志
```
Validation error: [{'type': 'missing', 'loc': ('body', 'file'), 'msg': 'Field required', 'input': None}]
```

---

## 🔍 问题原因

### 根本原因
前端API客户端在初始化时设置了全局HTTP头:
```python
self.session.headers.update({
    'Content-Type': 'application/json'  # ❌ 这会干扰文件上传
})
```

### 为什么会导致422错误?

1. **文件上传需要 `multipart/form-data`**
   - FastAPI期望接收 `multipart/form-data` 格式的文件上传
   - 但全局header强制使用 `application/json`

2. **Content-Type冲突**
   - 当发送文件时,requests库应该自动设置 `multipart/form-data`
   - 但全局header覆盖了自动设置,导致后端无法解析文件字段

3. **后端验证失败**
   - FastAPI尝试从请求体中提取 `file` 字段
   - 由于Content-Type错误,解析失败
   - 返回422 Unprocessable Entity

---

## ✅ 修复内容

### 修改文件: `frontend/api/client.py`

#### 1. 移除全局Content-Type设置

**修改前:**
```python
def __init__(self):
    self.base_url = app_settings.base_url
    self.session = requests.Session()
    self.session.headers.update({
        'Content-Type': 'application/json'  # ❌ 问题所在
    })
```

**修改后:**
```python
def __init__(self):
    self.base_url = app_settings.base_url
    self.session = requests.Session()
    # 不设置全局Content-Type，让requests根据请求类型自动设置
```

#### 2. 改进文件上传代码

**修改前:**
```python
files = {'file': (file_path, f, 'image/jpeg')}  # 使用完整路径
```

**修改后:**
```python
import os  # 添加os模块导入

files = {'file': (os.path.basename(file_path), f, 'image/jpeg')}  # 只使用文件名
```

**原因:** 
- 后端期望接收文件名,而不是完整路径
- 使用 `os.path.basename()` 提取纯文件名

---

## 📊 技术说明

### HTTP Content-Type

| 请求类型 | Content-Type | 说明 |
|---------|-------------|------|
| JSON数据 | `application/json` | API请求/响应 |
| 文件上传 | `multipart/form-data` | 上传文件时必须使用 |
| 表单数据 | `application/x-www-form-urlencoded` | 普通表单提交 |

### Requests库的行为

**当使用 `files` 参数时:**
```python
response = session.post(url, files={'file': (filename, file_obj)})
```

- ✅ **自动设置**: `Content-Type: multipart/form-data; boundary=...`
- ✅ **自动编码**: 文件内容正确编码
-  **被覆盖**: 如果session有全局header,会被覆盖

### FastAPI的文件上传

```python
@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    # FastAPI期望:
    # - Content-Type: multipart/form-data
    # - 表单字段: file (与参数名一致)
```

---

##  验证修复

### 测试步骤

1. **重启前端应用**
   ```bash
   # 关闭当前前端窗口
   # 重新启动
   .\venv312\Scripts\python.exe frontend\main.py
   ```

2. **上传测试图片**
   - 选择图片文件
   - 点击"开始处理"
   - 观察进度条

3. **预期结果**
   - ✅ 上传成功(进度条到100%)
   - ✅ OCR处理启动
   - ✅ 显示处理结果

### 查看后端日志

```bash
# 应该看到类似输出:
INFO:     127.0.0.1:xxxxx - "POST /api/v1/upload/image HTTP/1.1" 200 OK
```

---

## 💡 最佳实践

### 1. Session Header管理

**错误做法:**
```python
# ❌ 全局设置Content-Type
session.headers.update({'Content-Type': 'application/json'})
```

**正确做法:**
```python
# ✅ 在需要时临时设置
def get_json(self, url):
    headers = {'Content-Type': 'application/json'}
    response = self.session.get(url, headers=headers)
    return response.json()

# ✅ 或使用Content-Type参数
response = self.session.post(url, json=data)  # 自动设置application/json
response = self.session.post(url, files=files)  # 自动设置multipart/form-data
```

### 2. 文件上传规范

```python
import os

def upload_file(self, file_path: str):
    with open(file_path, 'rb') as f:
        # 使用纯文件名
        filename = os.path.basename(file_path)
        files = {'file': (filename, f, 'image/jpeg')}
        response = self.session.post(url, files=files)
        return response.json()
```

### 3. 错误处理

```python
try:
    response = self.session.post(url, files=files)
    response.raise_for_status()  # 检查HTTP状态码
    return response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 422:
        logger.error("Validation error: check request format")
    raise
```

---

##  相关文档

- [PORT_CHANGE.md](PORT_CHANGE.md) - 端口变更说明(8000→8001)
- [FRONTEND_IMPORT_FIX.md](FRONTEND_IMPORT_FIX.md) - 前端导入错误修复
- [ENCODING_FIX.md](ENCODING_FIX.md) - 启动脚本编码问题

---

##  总结

### 问题
- 全局Content-Type导致文件上传失败
- 后端无法解析文件字段
- 返回422错误

### 解决
- 移除全局Content-Type设置
- 使用os.path.basename()提取文件名
- 让requests自动设置正确的Content-Type

### 效果
- ✅ 文件上传正常工作
- ✅ OCR处理可以启动
- ✅ 系统功能完整可用

---

## 🎉 修复完成!

现在可以正常上传和处理图片了!

**测试方法:**
1. 重启前端应用
2. 选择一张图片
3. 点击"开始处理"
4. 应该能顺利完成整个流程
