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
        result = subprocess.run(cmd, shell=False, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd) if isinstance(cmd, (list,tuple)) else cmd}")
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

    build_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    print("Building Girl Packer with PyInstaller...")

    # Build via PyInstaller CLI with explicit --add-data mappings
    print("Preparing PyInstaller command with data files and hidden imports...")

    # Datas to include: map source -> dest inside bundle
    add_data = [
        (project_root / 'assets', 'assets'),
        (project_root / 'workflows', 'workflows'),
        (project_root / 'database', 'database'),
        (project_root / 'tools', 'tools'),
        (project_root / 'utils', 'utils'),
        (project_root / 'gui' / 'style.qss', 'gui'),
        (project_root / 'config.yaml', '.'),
        (project_root / 'ai', 'ai'),
    ]

    # Binaries to include
    add_binaries = [
        (project_root / 'ffmpeg.exe', '.'),
        (project_root / 'ffprobe.exe', '.'),
    ]

    # Hidden imports to help PyInstaller find dynamic imports
    hidden_imports = [
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
    ]

    # Build base command list
    pyinstaller_cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--onefile',
        '--console',
        '--name', 'GirlPacker',
        str(project_root / 'main.py')
    ]

    # Append data mappings
    for src, dest in add_data:
        if src.exists():
            mapping = f"{str(src)}{os.pathsep}{dest}"
            pyinstaller_cmd.extend(['--add-data', mapping])
        else:
            print(f"Warning: data source not found, skipping: {src}")

    # Append binary mappings
    for src, dest in add_binaries:
        if src.exists():
            mapping = f"{str(src)}{os.pathsep}{dest}"
            pyinstaller_cmd.extend(['--add-binary', mapping])
        else:
            print(f"Warning: binary source not found, skipping: {src}")

    # Append hidden imports
    for hi in hidden_imports:
        pyinstaller_cmd.extend(['--hidden-import', hi])

    print(f"Running PyInstaller build...")

    if run_command(pyinstaller_cmd):
        print("Build completed successfully!")
        exe_path = dist_dir / "GirlPacker.exe"
        if exe_path.exists():
            print(f"Executable created: {exe_path}")
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Size: {size_mb:.2f} MB")
        else:
            print("Warning: Executable not found in expected location")
    else:
        print("Build failed!")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())