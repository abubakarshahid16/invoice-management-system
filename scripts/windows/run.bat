@echo off
echo ============================================================
echo 🚗 Testing Web Server
echo ============================================================
echo.

:: Kill any existing Python processes
taskkill /F /IM python.exe 2>nul

:: Activate virtual environment and run test
call venv\Scripts\activate.bat
python run_test.py

pause 