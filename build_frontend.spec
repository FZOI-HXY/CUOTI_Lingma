# -*- mode: python ; coding: utf-8 -*-
"""
前端 PyInstaller spec 文件
用法: pyinstaller build_frontend.spec
"""

import os

block_cipher = None

# SPECPATH 是 PyInstaller 内置变量，指向 spec 文件所在目录
frontend_dir = os.path.join(SPECPATH, 'frontend')

datas = []

hiddenimports = [
    # PyQt6
    'PyQt6',
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.sip',
    # HTTP client
    'requests',
    'urllib3',
    # Image
    'PIL',
    # App modules
    'ui',
    'ui.main_window',
    'ui.upload_panel',
    'ui.question_manager',
    'ui.system_monitor',
    'ui.settings_dialog',
    'api',
    'api.client',
    'config',
    'config.settings',
    'utils',
    'widgets',
]

a = Analysis(
    [os.path.join(frontend_dir, 'main.py')],
    pathex=[frontend_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'pytest', 'IPython',
        'jupyter', 'notebook', 'matplotlib',
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
    exclude_binaries=True,
    name='cuoti_frontend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # 前端不需要控制台窗口
    icon=None,               # 可以后续添加 .ico 图标文件
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cuoti_frontend',
)
