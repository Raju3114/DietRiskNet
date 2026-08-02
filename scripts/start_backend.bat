@echo off
setlocal
REM ============================================================
REM DietRiskNet - start FastAPI backend
REM Uses the project-local virtual environment (recreated on each PC).
REM ============================================================

set "PROJECT_ROOT=%~dp0.."
for %%i in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fi"

echo ============================================================
echo  DietRiskNet - Backend
echo  Project root : %PROJECT_ROOT%
echo ============================================================

set "VENV_PY=%PROJECT_ROOT%\backend\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [ERROR] Virtual environment not found: %VENV_PY%
  echo         Run scripts\setup_new_pc.bat first to create it.
  exit /b 1
)

cd /d "%PROJECT_ROOT%"
echo [INFO] Starting FastAPI backend at http://localhost:8000
"%VENV_PY%" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
endlocal
