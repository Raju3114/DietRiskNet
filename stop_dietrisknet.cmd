@echo off
setlocal enabledelayedexpansion
rem ============================================================
rem  DietRiskNet - safe stop (stop_dietrisknet)
rem  Stops ONLY processes that (a) are LISTENING on a DietRiskNet
rem  service port (8000=backend, 3000=frontend, 11434=Ollama) AND
rem  (b) whose command line matches the expected DietRiskNet
rem  service pattern. It never kills arbitrary python/node/ollama.
rem ============================================================

echo Stopping DietRiskNet services...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports=@(8000,3000,11434);" ^
  "$procs=@();" ^
  "Get-NetTCPConnection -ErrorAction SilentlyContinue -State Listen | Where-Object { $ports -contains $_.LocalPort } | ForEach-Object { $p = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue -Filter ('ProcessId='+$_.OwningProcess); if ($p) { $cl=$p.CommandLine; if ($cl -match 'backend\.main' -or $cl -match 'uvicorn' -or $cl -match 'next' -or $cl -match 'ollama' -or $cl -match 'DietRiskNet') { $procs += $p } } };" ^
  "$u=$procs | Sort-Object ProcessId -Unique;" ^
  "if (@($u).Count -eq 0) { Write-Host '  No DietRiskNet services are running on ports 8000/3000/11434.' } else { foreach ($p in @($u)) { Write-Host ('  Stopping PID ' + $p.ProcessId + ' (' + $p.Name + ')'); Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } Write-Host ('  Stopped ' + @($u).Count + ' DietRiskNet process(es).') }"

if errorlevel 1 (
  echo   [WARN] stop command returned a non-zero exit code.
)
echo.
echo   DietRiskNet services stopped.
endlocal