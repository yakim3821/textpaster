@echo off
REM TextPaster Launcher
REM This script starts the TextPaster application

cd /d "%~dp0"

echo ============================================
echo   TextPaster - Template Manager
echo ============================================
echo.
echo Запуск приложения...
echo Starting application...
echo.

"C:\Program Files\Python313\python.exe" textpaster.py

if errorlevel 1 (
    echo.
    echo Ошибка при запуске приложения / Error starting application
    pause
)
