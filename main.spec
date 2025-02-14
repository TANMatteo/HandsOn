# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

mediapipe_datas = collect_data_files('mediapipe')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('custom_gestures.json', '.'),
        ('gui.py', '.'),
        ('hand_detector.py', '.'),
        ('sign_translator.py', '.'),
        ('text_to_speech.py', '.'),
        ('translations.py', '.'),
        ('video_source.py', '.'),
        ('Bonjour... en langue des signes.mp4', '.')
    ] + mediapipe_datas,
    hiddenimports=[
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        'numpy',
        'mediapipe',
        'pyttsx3',
    ] + collect_submodules('mediapipe'),
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
    name='main',
    debug=True,
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
    icon='NONE',
)
