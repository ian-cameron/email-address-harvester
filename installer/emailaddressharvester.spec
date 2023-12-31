# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['.\\..\src\\emailaddressharvester.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pyi_splash'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
splash = Splash(
    '.\\assets\\splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_color='red',
    text_pos=(20,460),
    text_size=20,
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    splash.binaries,
    [],
    name='emailaddressharvester',
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
    icon=['.\\assets\\icon.ico'],
)
