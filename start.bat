@echo off
echo ============================================================
echo 🚗 Mechanic Shop Invoice Management System
echo ============================================================
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Please run setup.bat first to set up the system.
    echo.
    pause
    exit /b 1
)

:: Kill any existing Python processes
taskkill /F /IM python.exe 2>nul

:: Activate virtual environment and run the app
echo Starting the application...
echo.
echo The browser should open automatically.
echo If it doesn't, try this URL:
echo http://127.0.0.1:4000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

:: Activate virtual environment and run the app
call venv\Scripts\activate.bat
python simple_app.py

if errorlevel 1 (
    echo.
    echo Error starting the application!
    echo Please make sure you ran setup.bat first.
    echo.
    pause
    exit /b 1
)

pause 