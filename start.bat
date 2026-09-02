@echo off
title SANGAM / BMIM Platform Runner
echo =========================================================
echo    SANGAM - Bharat Material Intelligence Network (BMIM)  
echo =========================================================
echo.

:: Launch Backend in separate window
echo [1/2] Launching Backend on http://localhost:8000 ...
start "SANGAM Backend (Port 8000)" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Launch Frontend in separate window
echo [2/2] Launching Frontend on http://localhost:5173 ...
start "SANGAM Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo =========================================================
echo   Servers running:
echo   - Frontend: http://localhost:5173
echo   - Backend:  http://localhost:8000/docs
echo   - Login:    admin@sangam.gov.in / admin_secure_password_2026
echo =========================================================
echo.

start http://localhost:5173
