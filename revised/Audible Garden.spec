# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)


a = Analysis(
    ['turntable_gui_.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.'), ('assets', 'assets')],
    hiddenimports=['cv2', 'numpy', 'PyQt5', 'pythonosc'],
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
    [],
    exclude_binaries=True,
    name='Audible Garden',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Audible Garden',
)
app = BUNDLE(
    coll,
    name='Audible Garden.app',
    icon=None,
    bundle_identifier=None,
)
