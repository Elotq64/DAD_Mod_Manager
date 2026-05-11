# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('src/assets/ffmpeg.exe', 'ffmpeg'),
        ('src/assets/ffprobe.exe', 'ffmpeg'),
        ('src/assets/unrar.exe', 'ffmpeg')
    ],
    datas=[('src/assets', 'src/assets')],
    hiddenimports=[
        'py7zr',
        'pyppmd',
        'pybcj',
        'multivolumefile',
        'inflate64',
        'pyzstd',
        'texttable',
        'brotli'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DAD_Mod_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['src\\assets\\icon.ico'],
)
