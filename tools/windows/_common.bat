@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Raiz del repo (tools\windows -> ..\..)
set "QL_ROOT=%~dp0..\.."
for %%I in ("%QL_ROOT%") do set "QL_ROOT=%%~fI"
cd /d "%QL_ROOT%" || (
  echo [ERROR] No se pudo cambiar al directorio del proyecto: %QL_ROOT%
  exit /b 1
)

if not exist "tools\windows\logs" mkdir "tools\windows\logs" >nul 2>&1
set "QL_LOG_DIR=%QL_ROOT%\tools\windows\logs"

rem Cargar .env sin imprimir valores
if exist ".env" (
  for /f "usebackq eol=# tokens=1* delims==" %%A in (".env") do (
    if not "%%A"=="" if not defined %%A set "%%A=%%B"
  )
)

rem Resolver Python / uv
set "QL_RUNNER="
set "QL_PY=python"
where uv >nul 2>&1 && set "QL_RUNNER=uv run"
if not defined QL_RUNNER (
  where python >nul 2>&1 && set "QL_RUNNER=PYTHONPATH=src python -m quantlab.brokers.binance.cli"
)
if not defined QL_RUNNER (
  echo [ERROR] No se encontro uv ni python en PATH.
  exit /b 127
)

rem Helper: ejecutar quantlab-testnet con el runner adecuado
set "QL_TESTNET_CMD=%QL_RUNNER% quantlab-testnet"
if "%QL_RUNNER%"=="uv run" (
  set "QL_TESTNET_CMD=uv run quantlab-testnet"
  set "QL_WORKBENCH_CMD=uv run quantlab-workbench"
) else (
  set "QL_TESTNET_CMD=set PYTHONPATH=src&& python -m quantlab.brokers.binance.cli"
  set "QL_WORKBENCH_CMD=set PYTHONPATH=src&& python -m quantlab.workbench.launch"
)

exit /b 0
