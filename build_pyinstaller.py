#!/usr/bin/env python3
"""
Build script for Girl Packer using PyInstaller
Creates a standalone executable with all dependencies and data files.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    project_root = Path(__file__).parent
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"

    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    build_dir.mkdir()
    dist_dir.mkdir()

    print("Building Girl Packer with PyInstaller...")

    # Create spec file content (full spec written as a string)
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

project_root = Path(r"{project_root}")

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Assets and data
        (str(project_root / 'assets'), 'assets'),
        (str(project_root / 'database'), 'database'),
        (str(project_root / 'gui' / 'style.qss'), 'style.qss'),
        (str(project_root / 'ffmpeg.exe'), 'ffmpeg.exe'),
        (str(project_root / 'ffprobe.exe'), 'ffprobe.exe'),
        (str(project_root / 'config.yaml'), 'config.yaml'),
        # AI models
        (str(project_root / 'ai' / 'models'), 'ai/models'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'torch',
        'torchvision',
        'ultralytics',
        'transparent_background',
        'loguru',
        'yaml',
        'cv2',
        'PIL',
        'numpy',
        'sklearn',
        'vlc',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GirlPacker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
""".format(project_root=str(project_root))

    spec_file = project_root / "girl_packer.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)

    # PyInstaller command
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print(f"Running PyInstaller build...")

    if run_command(pyinstaller_cmd):
        print("Build completed successfully!")
        exe_path = dist_dir / "GirlPacker.exe"
        if exe_path.exists():
            print(f"Executable created: {exe_path}")
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(".2f")
        else:
            print("Warning: Executable not found in expected location")
    else:
        print("Build failed!")
        return 1

    # Clean up spec file
    if spec_file.exists():
        spec_file.unlink()

    return 0

if __name__ == "__main__":
    sys.exit(main())