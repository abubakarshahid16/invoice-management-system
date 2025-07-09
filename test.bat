@echo off
echo ============================================================
echo 🚗 Testing Web Server
echo ============================================================
echo.
echo This will test if Flask is working correctly.
echo.
echo Try accessing: http://127.0.0.1:9000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

:: Kill any existing Python processes
taskkill /F /IM python.exe 2>nul

:: Run as administrator
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && call venv\Scripts\activate.bat && python test.py' -Verb RunAs"

pause 