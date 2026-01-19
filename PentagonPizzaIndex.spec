# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['flask', 'plotly', 'pandas', 'yfinance', 'livepopulartimes', 'werkzeug', 'jinja2']
hiddenimports += collect_submodules('yfinance')
hiddenimports += collect_submodules('plotly')


a = Analysis(
    ['D:\\download\\Pizza-Meter-Project\\The-Pizza-Meter\\src\\dashboard.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\download\\Pizza-Meter-Project\\The-Pizza-Meter\\src\\dashboard.py', '.')],
    hiddenimports=hiddenimports,
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
    name='PentagonPizzaIndex',
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
)
