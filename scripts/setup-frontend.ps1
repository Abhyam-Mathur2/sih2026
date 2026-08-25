# =============================================================
# BMIM – Frontend Setup Script (Windows PowerShell)
# =============================================================
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File scripts/setup-frontend.ps1
# =============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot  = Split-Path -Parent $PSScriptRoot
$FrontendDir  = Join-Path $ProjectRoot "frontend"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  BMIM Frontend Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------------
# 1. Check Node.js version
# ------------------------------------------------------------------
Write-Host "[1/3] Checking Node.js version..." -ForegroundColor Yellow
try {
    $nodeVersion = & node --version 2>&1
    Write-Host "      Found: $nodeVersion" -ForegroundColor Green
    $major = [int]($nodeVersion -replace "v", "").Split(".")[0]
    if ($major -lt 18) {
        Write-Host "      WARNING: Node.js 20+ is recommended (found $nodeVersion)." -ForegroundColor Yellow
    }
} catch {
    Write-Host "      ERROR: Node.js not found." -ForegroundColor Red
    Write-Host "             Install from https://nodejs.org (choose LTS version 20+)" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------
# 2. Check npm
# ------------------------------------------------------------------
Write-Host "[2/3] Checking npm..." -ForegroundColor Yellow
try {
    $npmVersion = & npm --version 2>&1
    Write-Host "      npm $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: npm not found." -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------
# 3. Install npm dependencies
# ------------------------------------------------------------------
Set-Location $FrontendDir
Write-Host "[3/3] Installing npm dependencies..." -ForegroundColor Yellow
npm install
Write-Host "      Dependencies installed." -ForegroundColor Green

# ------------------------------------------------------------------
# Copy .env if it doesn't exist
# ------------------------------------------------------------------
$envFile    = Join-Path $FrontendDir ".env"
$envExample = Join-Path $FrontendDir ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "      Created frontend/.env from .env.example." -ForegroundColor Green
    }
} else {
    Write-Host "      frontend/.env already exists – skipping." -ForegroundColor Green
}

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Frontend setup complete!" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step:" -ForegroundColor White
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/run-frontend.ps1" -ForegroundColor White
Write-Host ""
