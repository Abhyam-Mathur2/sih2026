# =============================================================
# BMIM – Backend Run Script (Windows PowerShell)
# =============================================================
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File scripts/run-backend.ps1
# =============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir  = Join-Path $ProjectRoot "backend"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  BMIM Backend Startup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------------
# Activate virtual environment
# ------------------------------------------------------------------
$VenvPath       = Join-Path $BackendDir ".venv"
$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "ERROR: .venv not found. Run setup-backend.ps1 first." -ForegroundColor Red
    exit 1
}
. $activateScript
Write-Host "Virtual environment activated." -ForegroundColor Green

# ------------------------------------------------------------------
# Check .env exists
# ------------------------------------------------------------------
$envFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "WARNING: $envFile not found." -ForegroundColor Yellow
    Write-Host "         Copying .env.example – please edit it before continuing." -ForegroundColor Yellow
    $envExample = Join-Path $BackendDir ".env.example"
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
    }
}

# ------------------------------------------------------------------
# Change to backend directory (alembic needs this)
# ------------------------------------------------------------------
Set-Location $BackendDir

# Refuse to start against an empty template rather than falling back to a
# nonexistent local PostgreSQL instance.
$databaseLine = Get-Content $envFile | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
if (-not $databaseLine -or $databaseLine -match 'YOUR_PROJECT|\[PASSWORD\]|^DATABASE_URL=$') {
    Write-Host "ERROR: Configure DATABASE_URL in backend/.env with your Supabase connection string." -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------
# Run Alembic migrations
# ------------------------------------------------------------------
Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Yellow
try {
    alembic upgrade head
    Write-Host "Migrations applied." -ForegroundColor Green
} catch {
    Write-Host "Migration failed: $_" -ForegroundColor Red
    Write-Host "Check Supabase connectivity and DATABASE_URL/DATABASE_URL_SYNC in backend/.env." -ForegroundColor Yellow
    exit 1
}

# ------------------------------------------------------------------
# Seed demo data
# ------------------------------------------------------------------
Write-Host ""
Write-Host "Seeding demo data (safe to run multiple times)..." -ForegroundColor Yellow
try {
    python -m app.db.seed
    Write-Host "Seed complete." -ForegroundColor Green
} catch {
    Write-Host "Seed step failed (non-fatal): $_" -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# Start FastAPI with uvicorn
# ------------------------------------------------------------------
Write-Host ""
Write-Host "Starting FastAPI backend..." -ForegroundColor Cyan
Write-Host "  API:     http://localhost:8000" -ForegroundColor White
Write-Host "  Swagger: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health:  http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
