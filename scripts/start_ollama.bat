@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM DietRiskNet - start project-local Ollama
REM Determines PROJECT_ROOT relative to this script (scripts\..)
REM so it works from any drive/folder.
REM Reuses an already-running server, waits until ready, then
REM verifies the configured model is installed.
REM ============================================================

set "PROJECT_ROOT=%~dp0.."
for %%i in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fi"

set "OLLAMA_EXE=%PROJECT_ROOT%\runtime\ollama\bin\ollama.exe"
set "OLLAMA_MODELS=%PROJECT_ROOT%\runtime\ollama\models"
set "OLLAMA_HOST=127.0.0.1:11434"

REM Read the configured model from .env (OLLAMA_MODEL), else the default.
set "OLLAMA_MODEL=llama3.2:3b"
if exist "%PROJECT_ROOT%\.env" (
  for /f "usebackq tokens=1,* delims==" %%a in ("%PROJECT_ROOT%\.env") do (
    if /i "%%a"=="OLLAMA_MODEL" set "OLLAMA_MODEL=%%b"
  )
)

echo ============================================================
echo  DietRiskNet - Local Ollama (project-local)
echo  Project root : %PROJECT_ROOT%
echo  Ollama exe   : %OLLAMA_EXE%
echo  Model dir    : %OLLAMA_MODELS%
echo  Model        : %OLLAMA_MODEL%
echo ============================================================

if not exist "%OLLAMA_EXE%" (
  echo [ERROR] Ollama executable not found: %OLLAMA_EXE%
  exit /b 1
)
if not exist "%OLLAMA_MODELS%\manifests" (
  echo [WARN] Model directory is empty. Pull the model:
  echo        "%OLLAMA_EXE%" pull %OLLAMA_MODEL%
)

REM Reuse an already-running server on port 11434 to avoid duplicates.
netstat -ano | findstr /C:":11434" | findstr /C:"LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [INFO] Ollama already running on port 11434 - reusing it.
  curl -s http://localhost:11434/api/version
  echo.
  goto verify_model
)

echo [INFO] Starting project-local Ollama...
start "DietRiskNet-Ollama" /min "%OLLAMA_EXE%" serve

echo [INFO] Waiting for Ollama to become ready...
set /a tries=0
:waitloop
ping -n 2 127.0.0.1 >nul
curl -s --max-time 2 http://localhost:11434/api/version >nul 2>&1
if errorlevel 1 (
  set /a tries+=1
  if !tries! lss 30 goto waitloop
  echo [ERROR] Ollama did not become ready in time.
  exit /b 1
)

echo [OK] Ollama ready:
curl -s http://localhost:11434/api/version
echo.

:verify_model
echo [INFO] Verifying model "%OLLAMA_MODEL%" is installed...
"%OLLAMA_EXE%" list > "%TEMP%\drn_ollama_list.txt" 2>nul
>nul 2>&1 findstr /I /C:"%OLLAMA_MODEL%" "%TEMP%\drn_ollama_list.txt"
if errorlevel 1 (
  echo.
  echo [ERROR] Required Ollama model "%OLLAMA_MODEL%" is not available.
  echo         Pull it with:
  echo            "%OLLAMA_EXE%" pull %OLLAMA_MODEL%
  echo.
  echo         The rest of DietRiskNet will still start, but AI features
  echo         will report unavailable until the model is installed.
  echo.
) else (
  echo [OK] Model "%OLLAMA_MODEL%" is available.
)

echo Backend expects Ollama at http://localhost:11434
endlocal