@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM DietRiskNet - start everything reliably:
REM   1) verify Python/backend environment
REM   2) Ollama  (reuse healthy; start + wait + verify model)
REM   3) Backend (reuse healthy; start + wait until ready)
REM   4) Frontend(reuse healthy; start + wait until ready)
REM Each service is reused if it is already healthy, so no duplicate
REM processes are spawned.  All waits are bounded (no infinite loops).
REM ============================================================

set "PROJECT_ROOT=%~dp0.."
for %%i in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fi"

echo ============================================================
echo  DietRiskNet - Start All
echo  Project root : %PROJECT_ROOT%
echo ============================================================

REM ---- 1) Verify Python / backend environment ----
set "VENV_PY=%PROJECT_ROOT%\backend\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [ERROR] backend\.venv not found: %VENV_PY%
  echo         Run scripts\setup_new_pc.bat first.
  exit /b 1
)
echo [OK] Backend environment ready.

REM ---- 2) Ollama (reuse / start / wait / verify model) ----
call "%~dp0start_ollama.bat"
if errorlevel 1 (
  echo [ERROR] Ollama failed to start. See messages above.
  exit /b 1
)

REM ---- 3) Backend (reuse if healthy, else start and wait) ----
curl -s --max-time 3 http://127.0.0.1:8000/ >nul 2>&1
if not errorlevel 1 (
  echo [INFO] Backend already healthy on port 8000 - reusing it.
  goto backend_ready
)
echo [INFO] Starting the backend...
start "DietRiskNet-Backend" cmd /k call "%~dp0start_backend.bat"
set /a tries=0
:wait_backend
ping -n 2 127.0.0.1 >nul
curl -s --max-time 2 http://127.0.0.1:8000/ >nul 2>&1
if errorlevel 1 (
  set /a tries+=1
  if !tries! lss 60 goto wait_backend
  echo [ERROR] Backend did not become ready in time on port 8000.
  exit /b 1
)
:backend_ready
echo [OK] Backend ready at http://127.0.0.1:8000  (API docs: /docs)

REM ---- 4) Frontend (reuse if healthy, else start and wait) ----
if exist "%PROJECT_ROOT%\frontend\node_modules\" (
  curl -s --max-time 3 http://localhost:3000/ >nul 2>&1
  if not errorlevel 1 (
    echo [INFO] Frontend already serving on port 3000 - reusing it.
    goto frontend_ready
  )
  echo [INFO] Starting Frontend...
  start "DietRiskNet-Frontend" cmd /k call "%~dp0start_frontend.bat"
  set /a tries=0
  :wait_frontend
  ping -n 2 127.0.0.1 >nul
  curl -s --max-time 2 http://localhost:3000/ >nul 2>&1
  if errorlevel 1 (
    set /a tries+=1
    if !tries! lss 60 goto wait_frontend
    echo [WARN] Frontend did not become ready in time on port 3000.
    exit /b 1
  )
) else (
  echo [ERROR] frontend\node_modules not found. Run scripts\setup_new_pc.bat first.
  exit /b 1
)
:frontend_ready
echo [OK] Frontend ready at http://localhost:3000

echo.
echo ============================================================
echo  DietRiskNet is ready:
echo    Ollama   http://localhost:11434   (AI provider)
echo    Backend  http://localhost:8000    (API docs: /docs)
echo    Frontend http://localhost:3000
echo ============================================================
echo  Open http://localhost:3000 in your browser.
endlocal