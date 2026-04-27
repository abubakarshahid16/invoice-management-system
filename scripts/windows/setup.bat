@echo off
echo ============================================================
echo 🚗 Setting up Mechanic Shop Invoice System
echo ============================================================
echo.

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment and install packages
echo Installing required packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install flask==2.0.1
pip install flask-sqlalchemy==2.5.1
pip install reportlab==3.6.8
pip install pillow==8.4.0
pip install python-dateutil==2.8.2

echo.
echo Setup complete! You can now run start.bat
echo.
pause 