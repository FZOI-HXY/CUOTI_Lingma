# PaddleOCR 使用指南

## 安装状态

✅ **PaddlePaddle**: 3.3.1  
✅ **PaddleOCR**: 3.6.0  
✅ **PaddleX**: 3.6.1  
✅ **Python**: 3.12.10 (虚拟环境: venv312)

---

## 快速开始

### 1. 激活虚拟环境

```powershell
.\venv312\Scripts\Activate.ps1
```

### 2. 验证安装

```powershell
python test_paddleocr.py
```

---

## 使用方法

### 方法一: 直接使用 PaddleOCR

```python
from paddleocr import PaddleOCR

# 初始化 OCR
ocr = PaddleOCR(lang='ch', show_log=False)

# 识别图片
result = ocr.ocr('path/to/image.jpg')

# 处理结果
for line in result[0]:
    text = line[1][0]        # 识别的文本
    confidence = line[1][1]   # 置信度 (0-1)
    box = line[0]             # 文本框坐标
    print(f"文本: {text}")
    print(f"置信度: {confidence:.4f}")
```

### 方法二: 使用项目的 OCR 服务

```python
from backend.app.services.ocr_service import OCRService

# 创建服务实例
ocr_service = OCRService()
ocr_service.initialize()

# 处理图片 (完整流程: 版面分析 + OCR + Markdown生成)
result = ocr_service.process_image('path/to/image.jpg')

# 获取结果
markdown_content = result['markdown_content']
processed_image_path = result['processed_image_path']
metadata = result['metadata']
```

### 方法三: 通过 API 使用

#### 启动后端服务

```powershell
cd backend
python -m app.main
```

#### API 调用示例

**1. 上传图片**

```python
import requests

url = "http://localhost:8001/upload/image"
files = {'file': open('test.jpg', 'rb')}
response = requests.post(url, files=files)
file_id = response.json()['file_id']
```

**2. 启动 OCR 处理**

```python
url = "http://localhost:8001/ocr/process"
data = {
    'file_id': file_id,
    'user_id': 1
}
response = requests.post(url, json=data)
task_id = response.json()['task_id']
```

**3. 查询任务状态**

```python
url = f"http://localhost:8001/ocr/status/{task_id}"
response = requests.get(url)
status = response.json()
print(f"进度: {status['progress']}%")
print(f"状态: {status['message']}")
```

### 方法四: 使用前端界面

```powershell
cd frontend
python main.py
```

在前端界面中:
1. 点击"选择图片文件"
2. 选择包含文字的图片
3. 点击"开始处理"
4. 查看 OCR 识别结果

---

## 配置说明

配置文件位置: `backend/app/config.py`

```python
# OCR 配置
OCR_LANG = "ch"          # 语言: ch(中文), en(英文)
OCR_USE_GPU = False      # 是否使用 GPU
OCR_DET_THRESH = 0.5     # 检测阈值
OCR_REC_THRESH = 0.8     # 识别阈值
```

---

## 支持的图片格式

- JPG/JPEG
- PNG
- BMP
- TIFF
- WEBP

---

## 常见问题

### 1. 首次运行速度慢

首次运行时，PaddleOCR 会自动下载模型文件（约 100MB），请耐心等待。

### 2. 识别精度不高

可以尝试:
- 提高图片质量
- 调整 `OCR_DET_THRESH` 和 `OCR_REC_THRESH`
- 确保图片中的文字清晰可见

### 3. 内存占用高

OCR 模型会占用较多内存（约 2-4GB），这是正常现象。

### 4. 如何切换到 GPU

如果您有 NVIDIA GPU:

1. 安装 CUDA 和 cuDNN
2. 修改配置: `OCR_USE_GPU = True`
3. 重新安装 GPU 版本的 PaddlePaddle:
   ```powershell
   pip uninstall paddlepaddle
   pip install paddlepaddle-gpu
   ```

---

## 测试示例

创建一个测试脚本 `test_simple.py`:

```python
from paddleocr import PaddleOCR
import os

# 检查是否有测试图片
test_image = "test.jpg"
if not os.path.exists(test_image):
    print(f"请准备一个测试图片: {test_image}")
    exit(1)

# 初始化并识别
print("正在初始化 PaddleOCR...")
ocr = PaddleOCR(lang='ch', show_log=False)

print(f"正在识别: {test_image}")
result = ocr.ocr(test_image)

print("\n识别结果:")
print("-" * 50)
for line in result[0]:
    text = line[1][0]
    confidence = line[1][1]
    print(f"[{confidence:.2f}] {text}")

print("\n完成!")
```

---

## 更多信息

- PaddleOCR 官方文档: https://github.com/PaddlePaddle/PaddleOCR
- PaddleX 官方文档: https://github.com/PaddlePaddle/PaddleX
- 项目 OCR 服务代码: `backend/app/services/ocr_service.py`

---

## 下一步

1. ✅ PaddleOCR 已安装完成
2. 📝 准备测试图片
3. 🚀 启动服务进行测试
4. 🔧 根据需求调整配置

祝您使用愉快！
