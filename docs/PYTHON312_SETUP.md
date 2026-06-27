# Python 3.12 虚拟环境设置指南

## 📋 前置条件

正在安装 Python 3.12.10...

## 🚀 完整步骤

### 步骤1: 等待Python 3.12安装完成

当前正在执行: `py install 3.12`

安装完成后,验证:
```bash
py -3.12 --version
```

应该显示: `Python 3.12.10`

### 步骤2: 创建虚拟环境

在项目根目录执行:

```bash
cd f:\CUOTI_Lingma

# 使用Python 3.12创建虚拟环境
py -3.12 -m venv venv_py312
```

### 步骤3: 激活虚拟环境

**Windows PowerShell:**
```bash
.\venv_py312\Scripts\Activate.ps1
```

**Windows CMD:**
```bash
.\venv_py312\Scripts\activate.bat
```

激活后,命令行前面会显示 `(venv_py312)`

### 步骤4: 升级pip

```bash
python -m pip install --upgrade pip
```

### 步骤5: 修改backend/requirements.txt

取消PaddleOCR相关包的注释:

编辑 `backend/requirements.txt`,将以下内容:
```txt
# OCR and Image Processing (暂时注释,需要Python 3.8-3.11)
# paddlepaddle==2.6.1
# paddleocr==2.7.3
# paddlex==3.0.0rc0
```

改为:
```txt
# OCR and Image Processing
paddlepaddle==2.6.1
paddleocr==2.7.3
paddlex==3.0.0rc0
```

**注意**: PaddlePaddle 2.6.1 支持 Python 3.8-3.11,对于Python 3.12可能需要使用更新版本。

### 步骤6: 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

如果PaddlePaddle 2.6.1不支持Python 3.12,尝试更新版本:
```bash
pip install paddlepaddle==2.6.2
# 或
pip install paddlepaddle
```

### 步骤7: 安装前端依赖

```bash
cd ..\frontend
pip install PyQt6 requests pillow
```

### 步骤8: 配置数据库

```bash
cd ..\backend
copy .env.example .env
```

编辑 `.env` 文件,设置MySQL连接信息。

### 步骤9: 初始化数据库

```bash
python ..\scripts\init_db.py
```

### 步骤10: 启动系统

**方式1: 分别启动**

终端1 - 后端:
```bash
cd backend
python -m app.main
```

终端2 - 前端(需要重新激活虚拟环境):
```bash
.\venv_py312\Scripts\Activate.ps1
cd frontend
python main.py
```

**方式2: 一键启动**
```bash
python scripts\start_services.py
```

## ⚠️ 常见问题

### 1. PaddlePaddle不支持Python 3.12

如果 `paddlepaddle==2.6.1` 安装失败,尝试:

```bash
# 尝试最新版本
pip install paddlepaddle

# 或使用CPU版本(更小)
pip install paddlepaddle-cpu

# 或降级到Python 3.11
py install 3.11
py -3.11 -m venv venv_py311
```

### 2. 虚拟环境激活失败

PowerShell执行策略问题:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. 退出虚拟环境

```bash
deactivate
```

### 4. 删除虚拟环境

```bash
Remove-Item -Recurse -Force venv_py312
```

## 📝 PaddlePaddle版本兼容性

| Python版本 | PaddlePaddle版本 | 状态 |
|-----------|-----------------|------|
| 3.8-3.11  | 2.6.1           | ✅ 完全支持 |
| 3.12      | 2.6.2+          | ⚠️ 需测试 |
| 3.12      | latest          | ✅ 推荐 |

## 🎯 推荐方案

**如果需要稳定的PaddleOCR功能:**

建议使用 **Python 3.11**,因为PaddlePaddle对3.11的支持最稳定:

```bash
# 安装Python 3.11
py install 3.11

# 创建虚拟环境
py -3.11 -m venv venv_py311

# 激活环境
.\venv_py311\Scripts\Activate.ps1

# 安装依赖
cd backend
pip install -r requirements.txt  # 取消PaddleOCR注释
```

## 🔍 验证安装

检查PaddlePaddle是否安装成功:

```bash
python -c "import paddle; print(paddle.__version__)"
```

检查PaddleOCR:

```bash
python -c "from paddleocr import PaddleOCR; print('PaddleOCR installed successfully')"
```

## 📊 当前进度

- [x] Python 3.12安装中...
- [ ] 创建虚拟环境
- [ ] 安装PaddlePaddle
- [ ] 安装其他依赖
- [ ] 配置数据库
- [ ] 启动系统

---

**提示**: Python 3.12下载可能需要几分钟时间,请耐心等待。下载完成后按照上述步骤操作即可。
