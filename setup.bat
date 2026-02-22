@echo off
REM PeakeCoin Bot Server Setup Script for Windows
REM This script sets up the environment and starts the bot server

echo ======================================
echo   PeakeCoin Bot Server Setup
echo ======================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

echo.
echo Setup complete!
echo Available options:
echo 1. Run GUI version: python main.py
echo 2. Run command-line version: python peake_droid.py
echo.
echo For server deployment:
echo - Copy this entire directory to your server
echo - Run this setup script on the server
echo - Use Task Scheduler or run as a service
echo.
pause
