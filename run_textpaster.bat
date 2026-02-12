@echo off
setlocal
cd /d "%~dp0"

REM Prefer GUI launchers to avoid console window.
where pyw >nul 2>&1
if %errorlevel%==0 (
    start "" /b pyw textpaster.pyw
    exit /b 0
)

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" /b pythonw textpaster.pyw
    exit /b 0
)

echo [TextPaster] pyw/pythonw not found. Falling back to python (console will be visible).
python textpaster.py
