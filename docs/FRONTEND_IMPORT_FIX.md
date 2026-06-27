# 前端导入错误修复说明

## 🔍 问题描述

### 错误1: 相对导入失败
```python
Traceback (most recent call last):
  File "F:\CUOTI_Lingma\frontend\main.py", line 6, in <module>
    from .ui.main_window import MainWindow
ImportError: attempted relative import with no known parent package
```

**原因:** `main.py`使用了相对导入(`from .ui...`),但直接运行时Python无法识别父包。

---

### 错误2: QAction导入位置错误
```python
ImportError: cannot import name 'QAction' from 'PyQt6.QtWidgets'
```

**原因:** PyQt6中`QAction`已从`QtWidgets`移到`QtGui`模块。

---

## ✅ 已完成的修复

### 1. 修复所有相对导入为绝对导入

#### frontend/main.py
```python
# 修复前
from .ui.main_window import MainWindow

# 修复后
from ui.main_window import MainWindow
```

#### frontend/ui/main_window.py
```python
# 修复前
from .upload_panel import UploadPanel
from .question_manager import QuestionManager
from .system_monitor import SystemMonitor
from .settings_dialog import SettingsDialog

# 修复后
from ui.upload_panel import UploadPanel
from ui.question_manager import QuestionManager
from ui.system_monitor import SystemMonitor
from ui.settings_dialog import SettingsDialog
```

#### frontend/ui/settings_dialog.py
```python
# 修复前
from ..config.settings import app_settings

# 修复后
from config.settings import app_settings
```

#### frontend/ui/question_manager.py
```python
# 修复前
from ..api.client import api_client

# 修复后
from api.client import api_client
```

#### frontend/ui/system_monitor.py
```python
# 修复前
from ..api.client import api_client

# 修复后
from api.client import api_client
```

#### frontend/ui/upload_panel.py
```python
# 修复前
from ..api.client import api_client

# 修复后
from api.client import api_client
```

#### frontend/api/client.py
```python
# 修复前
from ..config.settings import app_settings

# 修复后
from config.settings import app_settings
```

---

### 2. 修复QAction导入位置

#### frontend/ui/main_window.py
```python
# 修复前
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QMessageBox, QToolBar, QAction)
from PyQt6.QtGui import QIcon

# 修复后
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QMessageBox, QToolBar)
from PyQt6.QtGui import QIcon, QAction
```

---

## 📊 修复统计

| 文件 | 修复类型 | 数量 |
|------|---------|------|
| main.py | 相对导入→绝对导入 | 1处 |
| ui/main_window.py | 相对导入→绝对导入 + QAction位置 | 5处 |
| ui/settings_dialog.py | 相对导入→绝对导入 | 1处 |
| ui/question_manager.py | 相对导入→绝对导入 | 1处 |
| ui/system_monitor.py | 相对导入→绝对导入 | 1处 |
| ui/upload_panel.py | 相对导入→绝对导入 | 1处 |
| api/client.py | 相对导入→绝对导入 | 1处 |
| **总计** | - | **11处** |

---

## 💡 技术说明

### 为什么需要绝对导入?

当直接运行Python脚本时(如`python main.py`),该脚本不是作为包的一部分运行的,因此相对导入会失败。

**解决方案:**
- 使用绝对导入:`from ui.main_window import MainWindow`
- 或者使用`-m`参数运行:`python -m frontend.main`(需要__init__.py)

### PyQt6的QAction变化

在PyQt5中:
```python
from PyQt5.QtWidgets import QAction  # ✅ 正确
```

在PyQt6中:
```python
from PyQt6.QtWidgets import QAction  # ❌ 错误
from PyQt6.QtGui import QAction      # ✅ 正确
```

---

## 🎯 验证修复

### 测试前端启动
```bash
cd f:\CUOTI_Lingma
.\venv312\Scripts\python.exe frontend\main.py
```

**预期结果:**
- ✅ 无导入错误
- ✅ PyQt6窗口正常显示
- ✅ 可以连接到后端API (http://localhost:8001)

### 清理缓存(如果需要)
```powershell
# 删除所有__pycache__目录
Get-ChildItem -Path frontend -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
```

---

## 📝 最佳实践

### 1. 项目结构
```
frontend/
├── main.py              # 入口文件,使用绝对导入
├── config/
│   ├── __init__.py
│   └── settings.py
├── api/
│   ├── __init__.py
│   └── client.py
└── ui/
    ├── __init__.py
    ├── main_window.py
    ├── upload_panel.py
    └── ...
```

### 2. 导入规范
- **入口文件(main.py)**: 使用绝对导入
- **子模块**: 可以使用相对导入或绝对导入,但要一致
- **推荐**: 全部使用绝对导入,避免混淆

### 3. PyQt6注意事项
- `QAction` → `from PyQt6.QtGui import QAction`
- `QIcon` → `from PyQt6.QtGui import QIcon`
- 其他Widgets保持从`PyQt6.QtWidgets`导入

---

## 🔗 相关文档

- [PORT_CHANGE.md](PORT_CHANGE.md) - 端口变更说明(8000→8001)
- [ENCODING_FIX.md](ENCODING_FIX.md) - 启动脚本编码问题
- [FORCE_STOP_GUIDE.md](FORCE_STOP_GUIDE.md) - 强制停止服务指南

---

## 🎉 问题解决!

前端导入错误已全部修复,现在可以正常启动了!

**启动命令:**
```bash
# 方法1: 使用启动脚本(推荐)
.\start_en.bat

# 方法2: 手动启动前端
.\venv312\Scripts\python.exe frontend\main.py
```

前端会自动连接到后端API (http://localhost:8001)。
