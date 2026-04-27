@echo off
echo ============================================================
echo Mechanic Shop Invoice Management System
echo ============================================================
echo.

if not exist "venv" (
    echo Virtual environment not found.
    echo Run setup.bat first to create and configure it.
    echo.
    pause
    exit /b 1
)

taskkill /F /IM python.exe 2>nul

echo Starting the application...
echo.
echo Open this URL in your browser:
echo http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================
echo.

call venv\Scripts\activate.bat
python app.py

if errorlevel 1 (
    echo.
    echo Error starting the application.
    echo Make sure dependencies are installed and app.py exists.
    echo.
    pause
    exit /b 1
)

pause
