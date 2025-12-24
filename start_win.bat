@echo off
chcp 65001 > nul
echo ==========================================
echo       Sora Video Batch Generator
echo              (Windows)
echo ==========================================

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add it to PATH.
    pause
    exit /b 1
)

REM Check if venv exists, if not create it
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install requirements
if not exist "venv\Lib\site-packages\installed.flag" (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    echo done > venv\Lib\site-packages\installed.flag
)

REM Run the main script
echo [INFO] Starting Application...
python main.py %*

if %errorlevel% neq 0 (
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
) else (
    echo [INFO] Done.
    pause
)
