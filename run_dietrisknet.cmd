@echo off
setlocal enabledelayedexpansion

rem ============================================================
rem  DietRiskNet - one-command launcher  (run_dietrisknet)
rem  Self-locating via %~dp0. Reuses scripts\start_*.bat logic.
rem  Detects already-running services and reuses them (no dupes).
rem ============================================================

set "SCRIPT_DIR=%~dp0"
for %%i in ("%SCRIPT_DIR%") do set "PROJECT_ROOT=%%~fi"
set "OLLAMA_MODEL=llama3.2:3b"

echo ========================================
echo   DIETRISKNET STARTUP
echo ========================================
echo.

echo [1/6] Checking environment...
if not exist "%PROJECT_ROOT%\backend\.venv\Scripts\python.exe" (
  echo   [ERROR] Python venv not found: %PROJECT_ROOT%\backend\.venv\Scripts\python.exe
  echo           Run scripts\setup_new_pc.bat first.
  goto :bail
)
echo   Python / venv ......... OK

where npm >nul 2>&1
if errorlevel 1 (
  if exist "C:\Program Files\nodejs\npm.cmd" set "PATH=C:\Program Files\nodejs;%PATH%"
  if exist "%LOCALAPPDATA%\Programs\nodejs\npm.cmd" set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"
  if exist "C:\Program Files (x86)\nodejs\npm.cmd" set "PATH=C:\Program Files (x86)\nodejs;%PATH%"
  where npm >nul 2>&1
  if errorlevel 1 (
    echo   [ERROR] Node/npm not found. Install Node.js LTS from https://nodejs.org.
    goto :bail
  )
)
echo   Node / npm ............. OK
if not exist "%PROJECT_ROOT%\frontend\node_modules" (
  echo   [ERROR] frontend\node_modules missing. Run scripts\setup_new_pc.bat first.
  goto :bail
)
echo   Frontend deps .......... OK

set "FRESH=0"

echo.
echo [2/6] Ollama...
set "OLLAMA_OK=0"
call :check_ollama
if "!OLLAMA_OK!"=="1" (
  echo   [OK] Ollama already running
) else (
  echo   Starting Ollama...
  start "DietRiskNet-Ollama" cmd /k call "%PROJECT_ROOT%\scripts\start_ollama.bat"
  call :wait_ollama
  if "!OLLAMA_OK!"=="1" set "FRESH=1"
)
if "!OLLAMA_OK!"=="1" (
  echo   Ollama ............... READY   http://localhost:11434
  echo   Model ................ %OLLAMA_MODEL%
) else (
  echo   [ERROR] Ollama could not start / become ready.
)

echo.
echo [3/6] Backend...
set "BACKEND_OK=0"
call :check_backend
if "!BACKEND_OK!"=="1" (
  echo   [OK] Backend already running
) else (
  echo   Starting FastAPI...
  start "DietRiskNet-Backend" cmd /k call "%PROJECT_ROOT%\scripts\start_backend.bat"
  call :wait_backend
  if "!BACKEND_OK!"=="1" set "FRESH=1"
)
if "!BACKEND_OK!"=="1" (
  echo   FastAPI .............. READY   http://localhost:8000
) else (
  echo   [ERROR] Backend did not become ready. Inspect its window or backend\logs.
)

echo.
echo [4/6] Frontend...
set "FRONTEND_OK=0"
call :check_frontend
if "!FRONTEND_OK!"=="1" (
  echo   [OK] Frontend already running
) else (
  echo   Starting Next.js...
  call :start_frontend_window
  call :wait_frontend
  if "!FRONTEND_OK!"=="1" set "FRESH=1"
)
if "!FRONTEND_OK!"=="1" (
  echo   Next.js OK ............. READY   http://localhost:3000
) else (
  echo   [ERROR] Frontend did not become ready. Inspect its window.
)

echo.
echo [5/6] Health checks...
set "OLLAMA_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:11434/api/version 2^>nul') do if "%%c"=="200" set "OLLAMA_OK=1"
set "BACKEND_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:8000/ 2^>nul') do if "%%c"=="200" set "BACKEND_OK=1"
set "FRONTEND_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:3000/ 2^>nul') do if "%%c"=="200" set "FRONTEND_OK=1"
if "!OLLAMA_OK!"=="1" ( echo   Ollama ............ PASS ) else ( echo   Ollama ............ FAIL )
if "!BACKEND_OK!"=="1" ( echo   Backend ........... PASS ) else ( echo   Backend ........... FAIL )
if "!FRONTEND_OK!"=="1" ( echo   Frontend .......... PASS ) else ( echo   Frontend .......... FAIL )

echo.
if "!FRESH!"=="1" (
  echo ========================================
  echo   DIETRISKNET IS READY
  echo ========================================
) else (
  echo   DietRiskNet is already running - no duplicate services started.
)
echo   Frontend: http://localhost:3000
echo   Backend : http://localhost:8000
echo   Ollama  : http://localhost:11434
echo ========================================

if "!FRESH!"=="1" (
  echo.
  echo [6/6] Opening DietRiskNet in your browser...
  start "" "http://localhost:3000"
)
exit /b 0

rem ============================================================
rem  Helpers (forward-only references)
rem ============================================================
:check_ollama
set "OLLAMA_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:11434/api/version 2^>nul') do if "%%c"=="200" set "OLLAMA_OK=1"
exit /b 0

:wait_ollama
set /a tries=0
:ollama_wait
set "OLLAMA_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:11434/api/version 2^>nul') do if "%%c"=="200" set "OLLAMA_OK=1"
if "!OLLAMA_OK!"=="1" exit /b 0
set /a tries+=1
if !tries! gtr 60 exit /b 1
ping -n 2 127.0.0.1 >nul
goto ollama_wait

:check_backend
set "BACKEND_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:8000/ 2^>nul') do if "%%c"=="200" set "BACKEND_OK=1"
exit /b 0

:wait_backend
set /a tries=0
:backend_loop
set "BACKEND_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:8000/ 2^>nul') do if "%%c"=="200" set "BACKEND_OK=1"
if "!BACKEND_OK!"=="1" exit /b 0
set /a tries+=1
if !tries! gtr 90 exit /b 1
ping -n 2 127.0.0.1 >nul
goto backend_loop

:check_frontend
set "FRONTEND_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:3000/ 2^>nul') do if "%%c"=="200" set "FRONTEND_OK=1"
exit /b 0

:wait_frontend
set /a tries=0
:frontend_loop
set "FRONTEND_OK=0"
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" --max-time 3 http://localhost:3000/ 2^>nul') do if "%%c"=="200" set "FRONTEND_OK=1"
if "!FRONTEND_OK!"=="1" exit /b 0
set /a tries+=1
if !tries! gtr 120 exit /b 1
ping -n 2 127.0.0.1 >nul
goto frontend_loop

:start_frontend_window
start "DietRiskNet-Frontend" /min cmd /k call "%PROJECT_ROOT%\scripts\start_frontend.bat"
exit /b 0

:bail
echo.
echo   DietRiskNet could not start. See messages above.
exit /b 1