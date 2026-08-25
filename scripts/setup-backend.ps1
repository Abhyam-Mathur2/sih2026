# =============================================================
# BMIM – Backend Setup Script (Windows PowerShell)
# =============================================================
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File scripts/setup-backend.ps1
# =============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir  = Join-Path $ProjectRoot "backend"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  BMIM Backend Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------------
# 1. Check Python version
# ------------------------------------------------------------------
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
try {
    $pythonExe = "python"
    $pyVersion = & $pythonExe --version 2>&1
    Write-Host "      Found: $pyVersion" -ForegroundColor Green
    $major, $minor = ($pyVersion -replace "Python ", "").Split(".")[0..1]
    if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 11)) {
        Write-Host "      ERROR: Python 3.11+ is required." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "      ERROR: Python not found. Install Python 3.12 from https://python.org" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------
# 2. Create virtual environment
# ------------------------------------------------------------------
Set-Location $BackendDir
$VenvPath = Join-Path $BackendDir ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
    & $pythonExe -m venv .venv
    Write-Host "      Created: $VenvPath" -ForegroundColor Green
} else {
    Write-Host "[2/6] Virtual environment already exists – skipping creation." -ForegroundColor Green
}

# ------------------------------------------------------------------
# 3. Activate and upgrade pip/setuptools/wheel
# ------------------------------------------------------------------
Write-Host "[3/6] Activating venv and upgrading pip/setuptools/wheel..." -ForegroundColor Yellow
$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
. $activateScript
python -m pip install --upgrade pip setuptools wheel --quiet
Write-Host "      Done." -ForegroundColor Green

# ------------------------------------------------------------------
# 4. Install CPU-only PyTorch (avoids NVIDIA/CUDA packages)
# ------------------------------------------------------------------
Write-Host "[4/6] Installing CPU-only PyTorch..." -ForegroundColor Yellow
$reqCpu = Join-Path $BackendDir "requirements-cpu.txt"
if (Test-Path $reqCpu) {
    pip install -r $reqCpu --quiet
    Write-Host "      CPU-only torch installed." -ForegroundColor Green
} else {
    Write-Host "      requirements-cpu.txt not found – skipping torch pre-install." -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# 5. Install backend project (editable mode with dev extras)
# ------------------------------------------------------------------
Write-Host "[5/6] Installing backend project (pip install -e .[dev])..." -ForegroundColor Yellow
pip install -e ".[dev]" --quiet
Write-Host "      Installation complete." -ForegroundColor Green
python -c "import fastapi, sqlalchemy, sentence_transformers, pgvector, supabase; print('      Verified FastAPI, SQLAlchemy, CPU ML, pgvector and Supabase imports.')"

# ------------------------------------------------------------------
# 6. Copy .env if it doesn't exist
# ------------------------------------------------------------------
Write-Host "[6/6] Checking .env configuration..." -ForegroundColor Yellow
$envFile    = Join-Path $BackendDir ".env"
$envExample = Join-Path $BackendDir ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "      Created .env from .env.example." -ForegroundColor Green
        Write-Host "      IMPORTANT: Edit $envFile with your PostgreSQL credentials!" -ForegroundColor Magenta
    } else {
        Write-Host "      .env.example not found. Create $envFile manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "      .env already exists – skipping." -ForegroundColor Green
}

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Backend setup complete!" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Create a Supabase project (free tier is sufficient)." -ForegroundColor White
Write-Host "  2. Edit backend/.env with the Supabase database connection values." -ForegroundColor White
Write-Host "  3. Run: powershell -ExecutionPolicy Bypass -File scripts/run-backend.ps1" -ForegroundColor White
Write-Host ""
