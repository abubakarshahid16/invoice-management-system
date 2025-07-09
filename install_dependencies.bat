@echo off
echo ============================================================
echo 🚗 Installing Dependencies for Mechanic Shop System
echo ============================================================
echo.
echo This will install all required Python packages.
echo Please wait...
echo.

cd /d "%~dp0"

echo Installing Flask and dependencies...
pip install -r requirements.txt

echo.
echo ============================================================
echo ✅ Installation Complete!
echo ============================================================
echo.
echo You can now run the system by double-clicking: start_server.bat
echo.
pause 