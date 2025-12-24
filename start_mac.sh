#!/bin/bash

# Ensure we are in the script's directory
cd "$(dirname "$0")"

echo "=========================================="
echo "      CineFlow (影流) Video Pipeline"
echo "              (macOS/Linux)"
echo "=========================================="

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "[ERROR] Python 3 not found. Please install it."
    exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements if needed
if [ ! -f "venv/.installed_flag" ]; then
    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed_flag
fi

# Run
echo "[INFO] Starting Application..."
python main.py "$@"
