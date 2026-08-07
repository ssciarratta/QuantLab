@echo off
setlocal EnableExtensions EnableDelayedExpansion
title QuantLab - Test Binance Testnet Connection

call "%~dp0_common.bat" || exit /b 1
set "LOG=%QL_LOG_DIR%\03_testnet_connection_%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%.log"
set "LOG=%LOG: =0%"

echo.
echo ============================================================
echo  QuantLab - 03_test_binance_testnet_connection.bat
echo  Ping + time + autenticacion (sin ordenes).
echo  Log: %LOG%
echo ============================================================
echo.

(
  echo === quantlab-testnet ping ===
  call %QL_TESTNET_CMD% ping
  echo EXIT_PING=!ERRORLEVEL!
  echo.
  echo === quantlab-testnet balances (auth) ===
  call %QL_TESTNET_CMD% balances
  echo EXIT_BALANCES=!ERRORLEVEL!
) > "%LOG%" 2>&1

type "%LOG%"
findstr /C:"EXIT_PING=0" "%LOG%" >nul || exit /b 1
findstr /C:"EXIT_BALANCES=0" "%LOG%" >nul || exit /b 1

echo.
echo [OK] Conexion y autenticacion testnet verificadas.
exit /b 0
