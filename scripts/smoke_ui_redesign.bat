@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0\.."

set "PORT=8766"
set "BASE=http://127.0.0.1:%PORT%"
set "FAIL=0"
set "LOG=%TEMP%\ql_smoke_ui.log"

call :pass_init
echo == Smoke UI redesign (Windows) ==

echo [1] Archivos estaticos clave
for %%F in (
  "src\quantlab\workbench\static\js\panel_registry.js"
  "src\quantlab\workbench\static\js\ql_ui.js"
  "src\quantlab\workbench\static\js\panes\home.js"
  "src\quantlab\workbench\static\js\panes\monitor.js"
  "src\quantlab\workbench\static\css\design_tokens.css"
  "src\quantlab\workbench\static\css\friendly_ui.css"
) do (
  if exist "%%~F" (
    call :ok "%%~F"
  ) else (
    call :bad "missing %%~F"
  )
)

echo [2] Gate Python
uv run pytest tests/unit/execution/test_strategy_execution.py -q --tb=no
if errorlevel 1 (
  call :bad "pytest strategy_execution"
) else (
  call :ok "pytest strategy_execution"
)

echo [3] Servidor workbench :%PORT%
call :kill_port %PORT%
del /f /q "%LOG%" 2>nul
start /b "" cmd /c "uv run quantlab-workbench --no-browser --host 127.0.0.1 --port %PORT% >"%LOG%" 2>&1"

set "READY=0"
for /l %%I in (1,1,40) do (
  curl -sf "%BASE%/api/health" >nul 2>&1
  if not errorlevel 1 (
    set "READY=1"
    goto :server_up
  )
  ping -n 2 127.0.0.1 >nul
)
:server_up
if "!READY!"=="1" (
  call :ok "GET /api/health"
) else (
  call :bad "GET /api/health (server no respondio)"
  if exist "%LOG%" type "%LOG%"
)

echo [4] Static assets
for %%P in (
  "/static/js/panel_registry.js"
  "/static/js/ql_ui.js"
  "/static/js/panes/home.js"
  "/static/js/panes/monitor.js"
  "/static/css/friendly_ui.css"
  "/static/index.html"
) do (
  curl -sf "%BASE%%%~P" >nul 2>&1
  if errorlevel 1 (
    call :bad "GET %%~P"
  ) else (
    call :ok "GET %%~P"
  )
)

echo [5] index.html referencias
set "HTMLFILE=%TEMP%\ql_smoke_index.html"
curl -sf "%BASE%/static/index.html" -o "%HTMLFILE%" 2>nul
if exist "%HTMLFILE%" (
  findstr /i /c:"panel_registry.js" "%HTMLFILE%" >nul && call :ok "index - panel_registry" || call :bad "index - panel_registry"
  findstr /i /c:"home.js" "%HTMLFILE%" >nul && call :ok "index - home.js" || call :bad "index - home.js"
  findstr /i /c:"friendly_ui.css" "%HTMLFILE%" >nul && call :ok "index - friendly_ui" || call :bad "index - friendly_ui"
) else (
  call :bad "index.html download"
)

echo [6] Klines API (best-effort)
curl -sf --max-time 15 -X POST "%BASE%/api/lab/binance/klines" -H "Content-Type: application/json" -d "{\"symbol\":\"BTCUSDT\",\"interval\":\"1m\",\"limit\":5,\"market_type\":\"spot\"}" | findstr /c:"\"bars\"" >nul 2>&1
if errorlevel 1 (
  echo   WARN klines omitido ^(red Binance o timeout^)
  call :ok "POST klines skipped (offline ok)"
) else (
  call :ok "POST klines bars"
)

call :kill_port %PORT%

if "%FAIL%"=="0" (
  echo == SMOKE OK ==
  exit /b 0
)
echo == SMOKE FAILED ==
if exist "%LOG%" type "%LOG%"
exit /b 1

:ok
echo   OK  %~1
exit /b 0

:bad
echo   FAIL %~1
set "FAIL=1"
exit /b 0

:pass_init
exit /b 0

:kill_port
for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%~1 " ^| findstr LISTENING') do (
  taskkill /PID %%A /F >nul 2>&1
)
exit /b 0
