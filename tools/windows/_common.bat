@echo off
rem Shared bootstrap for tools\windows\*.bat
rem Variables must survive after this script returns (no sticky setlocal).

rem Raiz del repo (tools\windows -> ..\..)
set "QL_ROOT=%~dp0..\.."
for %%I in ("%QL_ROOT%") do set "QL_ROOT=%%~fI"
cd /d "%QL_ROOT%" || (
  echo [ERROR] No se pudo cambiar al directorio del proyecto: %QL_ROOT%
  exit /b 1
)

if not exist "tools\windows\logs" mkdir "tools\windows\logs" >nul 2>&1
set "QL_LOG_DIR=%QL_ROOT%\tools\windows\logs"

rem Stamp locale-independent for log filenames
set "QL_STAMP="
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "QL_STAMP=%%I"
if not defined QL_STAMP set "QL_STAMP=unknown"

rem Cargar .env sin imprimir valores (solo si la var aun no esta definida)
if exist ".env" (
  for /f "usebackq eol=# tokens=1* delims==" %%A in (".env") do (
    if not "%%A"=="" if not defined %%A set "%%A=%%B"
  )
)

rem Preferir venv local para evitar que "uv run" intente reescribir Scripts/*.exe
rem mientras Workbench tiene el archivo bloqueado.
set "QL_PY="
if exist "%QL_ROOT%\.venv\Scripts\python.exe" set "QL_PY=%QL_ROOT%\.venv\Scripts\python.exe"
if not defined QL_PY if exist "%QL_ROOT%\venv\Scripts\python.exe" set "QL_PY=%QL_ROOT%\venv\Scripts\python.exe"

if defined QL_PY (
  set "PYTHONPATH=%QL_ROOT%\src;%PYTHONPATH%"
  set "QL_TESTNET_CMD=%QL_PY% -m quantlab.brokers.binance.cli"
  set "QL_WORKBENCH_CMD=%QL_PY% -m quantlab.workbench.launch"
  exit /b 0
)

where uv >nul 2>&1
if not errorlevel 1 (
  set "QL_TESTNET_CMD=uv run quantlab-testnet"
  set "QL_WORKBENCH_CMD=uv run quantlab-workbench"
  exit /b 0
)

where python >nul 2>&1
if not errorlevel 1 (
  set "PYTHONPATH=%QL_ROOT%\src;%PYTHONPATH%"
  set "QL_TESTNET_CMD=python -m quantlab.brokers.binance.cli"
  set "QL_WORKBENCH_CMD=python -m quantlab.workbench.launch"
  exit /b 0
)

echo [ERROR] No se encontro .venv, uv ni python en PATH.
exit /b 127
