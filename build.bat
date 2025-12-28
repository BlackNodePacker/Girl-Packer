@echo off
REM Build script for Girl Packer
REM Usage: build.bat [nuitka|pyinstaller|setup|clean]

if "%1"=="nuitka" goto nuitka
if "%1"=="pyinstaller" goto pyinstaller
if "%1"=="setup" goto setup
if "%1"=="clean" goto clean

REM Default to PyInstaller for reliability
echo No option specified, defaulting to PyInstaller build...
goto pyinstaller

echo Usage: build.bat [nuitka^|pyinstaller^|setup^|clean]
echo.
echo nuitka     - Build with Nuitka (requires MSVC or MinGW)
echo pyinstaller- Build with PyInstaller (recommended)
echo setup      - Install in development mode
echo clean      - Clean build artifacts
goto end

:nuitka
echo Building with Nuitka...
echo Note: Ensure MSVC (Visual Studio Build Tools) or MinGW is installed for C compilation.
python build_nuitka.py
goto end

:pyinstaller
echo Building with PyInstaller...
python build_pyinstaller.py
goto end

:setup
echo Installing in development mode...
pip install -e .
goto end

:clean
echo Cleaning build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec
echo Cleaned.
goto end

:end