# Swift Event Intelligence Platform — Local Start (Windows PowerShell)
# Usage:  .\start.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Swift Event Intelligence Platform" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate venv if it exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "[1/2] Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "[1/2] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
    Write-Host "       Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
}

Write-Host "[2/2] Starting Swift platform..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  API + Swagger:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Health check:   http://localhost:8000/health" -ForegroundColor Green
Write-Host "  Login:          admin / SwiftAdmin2026!" -ForegroundColor Green
Write-Host ""

python run_local.py
