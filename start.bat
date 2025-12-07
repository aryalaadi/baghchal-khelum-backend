@echo off
echo ========================================
echo BaghChal Backend Startup Script
echo ========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.12 or higher
    pause
    exit /b 1
)
echo.

echo Checking if dependencies are installed...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Dependencies already installed
)
echo.

echo ========================================
echo IMPORTANT: Make sure the following are running:
echo 1. PostgreSQL (localhost:5432)
echo 2. Redis (localhost:6379)
echo ========================================
echo.

echo Press any key to start the server...
pause >nul

echo.
echo Starting BaghChal Backend Server...
echo Server will be available at: http://localhost:8000
echo Test UI: http://localhost:8000/tests/static_test_ui.html
echo API Docs: http://localhost:8000/docs
echo.

python main.py
