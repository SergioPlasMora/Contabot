# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Datos\\PDS\\python\\Contabot\\src\\luzzi\\contabot.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Datos\\PDS\\python\\Contabot\\img', 'img'), ('C:\\Datos\\PDS\\python\\Contabot\\config.yaml', '.'), ('C:\\Datos\\PDS\\python\\Contabot\\filters.yaml', '.'), ('C:\\Datos\\PDS\\python\\Contabot\\src\\data', 'data'), ('C:\\Datos\\PDS\\python\\Contabot\\src\\config', 'config'), ('C:\\Datos\\PDS\\python\\Contabot\\src\\luzzi\\helpers', 'helpers'), ('C:\\Datos\\PDS\\python\\Contabot\\src\\utils', 'utils'), ('C:\\Datos\\PDS\\python\\Contabot\\src\\luzzi\\page_objects', 'page_objects'), ('C:\\Datos\\PDS\\python\\Contabot\\src\\luzzi\\processors', 'processors'), ('C:\\Datos\\PDS\\python\\Contabot\\src\\commands', 'commands')],
    hiddenimports=['comtypes.stream', 'comtypes.client', 'pywinauto', 'cv2', 'cv2.data', 'cv2.cv2', 'dotenv', 'dotenv.main'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='contabot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:\\Datos\\PDS\\python\\Contabot\\public\\version_info.txt',
    icon=['C:\\Datos\\PDS\\python\\Contabot\\public\\Luzzi.ico'],
)
