#!/usr/bin/env python3
"""
Build script for Girl Packer using Nuitka
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

    print("Building Girl Packer with Nuitka...")

    # Nuitka command
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",  # Single executable
        "--enable-plugin=pyside6",
        "--enable-plugin=torch",
        "--assume-yes-for-downloads",
        "--output-dir=dist",
        "--output-filename=GirlPacker.exe",
        # Include data files
        "--include-data-dir=assets=assets",
        "--include-data-dir=database=database",
        "--include-data-file=gui/style.qss=style.qss",  # Copy to root for Nuitka fallback
        "--include-data-file=ffmpeg.exe=ffmpeg.exe",
        "--include-data-file=ffprobe.exe=ffprobe.exe",
        "--include-data-file=config.yaml=config.yaml",
        # Model files
        "--include-data-dir=ai/models=ai/models",
        # Python packages data
        "--include-package-data=torch",
        "--include-package-data=torchvision",
        "--include-package-data=ultralytics",
        "--include-package-data=transparent-background",
        # Disable console for GUI app
        "--windows-disable-console",
        # Optimization
        "--lto=yes",
        "--remove-output",
        "main.py"
    ]

    cmd_str = " ".join(nuitka_cmd)
    print(f"Running: {cmd_str}")

    if run_command(cmd_str):
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

    return 0

if __name__ == "__main__":
    sys.exit(main())