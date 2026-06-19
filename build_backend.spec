# -*- mode: python ; coding: utf-8 -*-
"""
后端 PyInstaller spec 文件
用法: pyinstaller build_backend.spec
"""

import os
import sys

block_cipher = None

# SPECPATH 是 PyInstaller 内置变量，指向 spec 文件所在目录
backend_dir = SPECPATH
app_dir = os.path.join(backend_dir, 'backend', 'app')

# 需要打包的数据文件
datas = [
    # 配置文件
    (os.path.join(backend_dir, 'backend', 'app', 'configs', 'PP-StructureV3.yaml'), 'app/configs'),
]

# 隐式导入（PyInstaller 无法自动发现的模块）
hiddenimports = [
    # FastAPI / uvicorn
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'pydantic_settings',
    'starlette',
    'starlette.middleware',
    'starlette.middleware.cors',
    'anyio',
    'anyio._backends',
    'anyio._backends._asyncio',
    'h11',
    'httptools',
    'websockets',
    'multipart',
    # SQLAlchemy
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'alembic',
    # PaddlePaddle / PaddleX
    'paddle',
    'paddle.base',
    'paddlex',
    'paddleocr',
    'paddleocr._pipelines',
    'paddleocr._pipelines.paddleocr_vl',
    'paddleocr._pipelines.base',
    # VL 增强模式依赖 (genai-client 插件)
    'openai',
    'httpx',
    'sniffio',
    'jiter',
    'distro',
    # Report
    'fpdf',
    'markdown',
    'matplotlib',
    'matplotlib.backends.backend_agg',
    # Image
    'PIL',
    'cv2',
    'numpy',
    # Utilities
    'loguru',
    'psutil',
    'aiofiles',
    'dotenv',
    # App modules
    'app',
    'app.main',
    'app.config',
    'app.database',
    'app.models',
    'app.schemas',
    'app.routers',
    'app.routers.upload',
    'app.routers.ocr',
    'app.routers.questions',
    'app.routers.system',
    'app.routers.reports',
    'app.services',
    'app.services.ocr_service',
    'app.services.report_service',
    'app.services.image_service',
    'app.services.storage_service',
    'app.services.markdown_service',
    'app.services.vl_service',
    'app.core',
    'app.core.exceptions',
    'app.utils',
    'app.utils.logger',
    'app.utils.validators',
]

a = Analysis(
    [os.path.join(backend_dir, 'backend', 'app', 'main.py')],
    pathex=[os.path.join(backend_dir, 'backend')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'pytest', 'IPython',
        'jupyter', 'notebook', 'matplotlib.tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # 文件夹模式（不打包为单文件）
    name='cuoti_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,            # 后端需要控制台输出日志
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cuoti_backend',
)
