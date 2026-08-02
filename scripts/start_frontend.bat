@echo off
setlocal
REM ============================================================
REM DietRiskNet - start Next.js frontend
REM Locates node/npm without relying on the global PATH so the
REM project runs even when Node is installed to a standard location
REM that is not on PATH (e.g. C:\Program Files\nodejs).
REM ============================================================

set "PROJECT_ROOT=%~dp0.."
for %%i in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fi"

echo ============================================================
echo  DietRiskNet - Frontend
echo  Project root : %PROJECT_ROOT%
echo ============================================================

REM Add the most common Node install locations to PATH if npm is not visible.
where npm >nul 2>&1
if errorlevel 1 (
  if exist "C:\Program Files\nodejs\npm.cmd" set "PATH=C:\Program Files\nodejs;%PATH%"
  if exist "%LOCALAPPDATA%\Programs\nodejs\npm.cmd" set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"
  if exist "C:\Program Files (x86)\nodejs\npm.cmd" set "PATH=C:\Program Files (x86)\nodejs;%PATH%"
  where npm >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] npm not found. Install Node.js LTS from https://nodejs.org.
    exit /b 1
  )
)

if not exist "%PROJECT_ROOT%\frontend\node_modules\" (
  echo [ERROR] frontend\node_modules not found.
  echo         Run scripts\setup_new_pc.bat first to install dependencies.
  exit /b 1
)

cd /d "%PROJECT_ROOT%\frontend"
echo [INFO] Starting Next.js at http://localhost:3000
call npm run dev
endlocal