@echo off
setlocal EnableExtensions
title QuantLab - Show Testnet Balances

call "%~dp0_common.bat" || exit /b 1
echo.
echo ============================================================
echo  QuantLab - 04_show_testnet_balances.bat
echo  Balances Spot Testnet (solo lectura).
echo ============================================================
echo.

%QL_TESTNET_CMD% balances
if errorlevel 1 (
  echo [ERROR] No se pudieron leer balances. Ejecute 02 y 03 primero.
  exit /b 1
)

echo.
echo [OK] Balances mostrados.
exit /b 0
