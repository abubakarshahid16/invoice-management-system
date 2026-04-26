@echo off
echo ============================================================
echo Mechanic Shop Invoice Management System
echo ============================================================
echo Starting the application...
echo.
echo The system will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================
echo.

cd /d "%~dp0"
python app.py

pause
