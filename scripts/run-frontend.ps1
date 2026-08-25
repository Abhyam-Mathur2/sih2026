# =============================================================
# BMIM – Frontend Run Script (Windows PowerShell)
# =============================================================
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File scripts/run-frontend.ps1
# =============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  BMIM Frontend Startup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------------
# Check node_modules exists
# ------------------------------------------------------------------
$nodeModules = Join-Path $FrontendDir "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "node_modules not found. Running npm install first..." -ForegroundColor Yellow
    Set-Location $FrontendDir
    npm install
}

Set-Location $FrontendDir

# ------------------------------------------------------------------
# Ensure .env exists
# ------------------------------------------------------------------
$envFile    = Join-Path $FrontendDir ".env"
$envExample = Join-Path $FrontendDir ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "Created frontend/.env from .env.example." -ForegroundColor Green
    } else {
        Write-Host "WARNING: frontend/.env not found. API calls may fail." -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------------
# Start Vite dev server
# ------------------------------------------------------------------
Write-Host "Starting Vite dev server..." -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend must be running at: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

npm run dev
