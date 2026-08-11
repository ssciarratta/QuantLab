@echo off
setlocal EnableExtensions
title QuantLab - Setup Testnet Environment

call "%~dp0_common.bat" || exit /b 1
echo.
echo ============================================================
echo  QuantLab - 01_setup_testnet_environment.bat
echo  Prepara dependencias Python (uv sync) y verifica CLI.
echo ============================================================
echo.

if exist "uv.lock" (
  echo [1/3] uv sync...
  uv sync
  if errorlevel 1 (
    echo [ERROR] uv sync fallo.
    exit /b 1
  )
) else (
  echo [WARN] uv.lock no encontrado; intentando pip install -e .
  python -m pip install -e ".[dev]"
  if errorlevel 1 exit /b 1
)

echo [2/3] Verificando quantlab-testnet...
%QL_TESTNET_CMD% status
if errorlevel 1 (
  echo [ERROR] quantlab-testnet no disponible.
  exit /b 1
)

echo [3/3] Verificando .gitignore excluye .env...
findstr /C:".env" .gitignore >nul 2>&1
if errorlevel 1 (
  echo [WARN] .env no aparece en .gitignore; revisar antes de commitear secrets.
) else (
  echo OK: .env esta en .gitignore.
)

echo.
echo [OK] Entorno preparado. Siguiente: 02_configure_testnet_credentials.bat
exit /b 0
