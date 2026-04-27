@echo off
echo ============================================================
echo 🚗 Starting Minimal Test Server
echo ============================================================
echo.

:: Kill any existing Python processes
taskkill /F /IM python.exe 2>nul

:: Run the minimal test
python minimal.py

pause 