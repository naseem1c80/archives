# app.spec
# احرص على وضع هذا الملف بجانب app.py

# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# المسارات للمجلدات الخارجية
project_path = os.path.abspath(".")
tess_path = os.path.join(project_path, "Tesseract-OCR")
upload_path = os.path.join(project_path, "uploads")

a = Analysis(
    ['app.py'],
    pathex=[project_path],
    binaries=[],
    datas=[
	    ('templates', 'templates'),
        (tess_path, 'Tesseract-OCR'),  # نسخ مجلد Tesseract
        (upload_path, 'uploads')       # نسخ مجلد uploads
    ],
    hiddenimports=collect_submodules('pytesseract'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # اجعله False إذا كنت لا تريد نافذة سوداء
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='app'
)
