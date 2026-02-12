@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo [TextPaster] Building EXE with PyInstaller (windowed mode, no console)...

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name TextPaster ^
  textpaster.py

if errorlevel 1 (
  echo [TextPaster] Build failed.
  exit /b 1
)

echo [TextPaster] Build complete: dist\TextPaster.exe
