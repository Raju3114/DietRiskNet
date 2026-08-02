@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM DietRiskNet - setup on a NEW Windows laptop after copying the
REM project (e.g. from an external HDD).
REM
REM - Recreates backend/.venv and frontend/node_modules (they are NOT
REM   portable and must be regenerated on this machine).
REM - Verifies the project-local Ollama runtime + model.
REM - Never installs system software silently.
REM ============================================================

set "PROJECT_ROOT=%~dp0.."
for %%i in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fi"

echo ============================================================
echo  DietRiskNet - New PC setup
echo  Project root : %PROJECT_ROOT%
echo ============================================================

REM ---- 1) Python ----
echo [1/7] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found on PATH.
  echo         Install Python 3.10+ from https://www.python.org/downloads/
  echo         (tick "Add python.exe to PATH"), then re-run this script.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   Found: %%v

REM ---- 2) Node.js ----
echo [2/7] Checking Node.js / npm...
where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js not found on PATH.
  echo         Install Node.js LTS from https://nodejs.org/ then re-run.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do echo   Node: %%v
where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found. Reinstall Node.js LTS.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('npm --version') do echo   npm: %%v

REM ---- 3/4) Backend virtual environment + requirements ----
echo [3/7] Checking backend virtual environment...
set "VENV_PY=%PROJECT_ROOT%\backend\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo   [INFO] Creating backend\.venv ...
  cd /d "%PROJECT_ROOT%\backend"
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create the virtual environment.
    pause
    exit /b 1
  )
  echo   [INFO] Installing backend requirements (this can take a while)...
  "%VENV_PY%" -m pip install --upgrade pip
  "%VENV_PY%" -m pip install -r "%PROJECT_ROOT%\requirements.txt"
  if errorlevel 1 (
    echo [ERROR] pip install failed. Check the messages above.
    pause
    exit /b 1
  )
) else (
  echo   [OK] backend\.venv already present.
)

REM ---- 5) Frontend dependencies ----
echo [4/7] Checking frontend dependencies...
if not exist "%PROJECT_ROOT%\frontend\node_modules\" (
  echo   [INFO] Running npm install in frontend ...
  cd /d "%PROJECT_ROOT%\frontend"
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
) else (
  echo   [OK] frontend\node_modules already present.
)

REM ---- 6) Project-local Ollama executable ----
echo [5/7] Checking project-local Ollama executable...
set "OLLAMA_EXE=%PROJECT_ROOT%\runtime\ollama\bin\ollama.exe"
if not exist "%OLLAMA_EXE%" (
  echo [ERROR] runtime\ollama\bin\ollama.exe not found.
  echo         Copy the runtime\ollama folder from the source machine
  echo         (or install Ollama and copy bin\ + lib\ into runtime\ollama).
  pause
  exit /b 1
) else (
  echo   [OK] "%OLLAMA_EXE%"
)

REM ---- 7) Ollama model directory + llama3.2:3b ----
echo [6/7] Checking project-local model...
if not exist "%PROJECT_ROOT%\runtime\ollama\models\manifests" (
  echo   [WARN] runtime\ollama\models is empty. Either copy it from the
  echo         source machine, or pull the model after starting Ollama:
  echo         "%OLLAMA_EXE%" pull llama3.2:3b
) else (
  echo   [OK] runtime\ollama\models present.
)

REM ---- .env ----
echo [7/7] Checking .env...
if not exist "%PROJECT_ROOT%\.env" (
  echo   [WARN] .env not found.
  echo         Copy it from the source machine (it is not in git), or
  echo         create one from .env.example.
) else (
  echo   [OK] .env present.
)

echo.
echo ============================================================
echo  Setup complete.
echo  Next steps:
echo    1. scripts\start_all.bat
echo    2. Open http://localhost:3000
echo ============================================================
pause
endlocal
