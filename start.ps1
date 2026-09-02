# ==============================================================================
# SANGAM / BMIM — Unified Startup Script (PowerShell)
# ==============================================================================
# This script starts:
#   1. FastAPI Backend server on http://localhost:8000
#   2. React + Vite Frontend server on http://localhost:5173
# ==============================================================================

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   SANGAM · Bharat Material Intelligence Network (BMIM)  " -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Ensure backend .env exists or use defaults
if (-not (Test-Path (Join-Path $BackendDir ".env"))) {
    Write-Host "[INFO] backend/.env not found, creating local SQLite default..." -ForegroundColor Yellow
    @"
DATABASE_URL=sqlite+aiosqlite:///./sangam.db
DEBUG=true
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
VECTOR_BACKEND=local
STORAGE_BACKEND=local
"@ | Out-File -FilePath (Join-Path $BackendDir ".env") -Encoding utf8
}

# Ensure frontend .env exists
if (-not (Test-Path (Join-Path $FrontendDir ".env"))) {
    Write-Host "[INFO] frontend/.env not found, creating default..." -ForegroundColor Yellow
    "VITE_API_BASE_URL=http://localhost:8000/api/v1" | Out-File -FilePath (Join-Path $FrontendDir ".env") -Encoding utf8
}

Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$BackendProcess = Start-Process python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $BackendDir -PassThru

Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Green
$FrontendProcess = Start-Process npm -ArgumentList "run dev" -WorkingDirectory $FrontendDir -PassThru

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  Services Started Successfully!                         " -ForegroundColor Green
Write-Host "  * Frontend UI:    http://localhost:5173                " -ForegroundColor Yellow
Write-Host "  * API & Swagger:  http://localhost:8000/docs           " -ForegroundColor Yellow
Write-Host "  * Credentials:    admin@sangam.gov.in                  " -ForegroundColor White
Write-Host "                    admin_secure_password_2026           " -ForegroundColor White
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C or close this terminal to stop both servers." -ForegroundColor Gray
Write-Host ""

# Automatically open browser
Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

# Wait for process exit or user cancellation
try {
    while ($true) {
        if ($BackendProcess.HasExited) {
            Write-Host "[WARN] Backend process exited." -ForegroundColor Red
            break
        }
        if ($FrontendProcess.HasExited) {
            Write-Host "[WARN] Frontend process exited." -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Both servers stopped." -ForegroundColor Green
}
