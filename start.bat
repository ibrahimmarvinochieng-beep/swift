@echo off
REM Swift Event Intelligence Platform — Local Start (Windows CMD)
REM Usage:  start.bat

echo.
echo ========================================
echo   Swift Event Intelligence Platform
echo ========================================
echo.

if exist venv\Scripts\activate.bat (
    echo [1/2] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [1/2] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo        Installing dependencies...
    pip install -r requirements.txt --quiet
)

echo [2/2] Starting Swift platform...
echo.
echo   API + Swagger:  http://localhost:8000/docs
echo   Health check:   http://localhost:8000/health
echo   Login:          admin / SwiftAdmin2026!
echo.

python run_local.py
