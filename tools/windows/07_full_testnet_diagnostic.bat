@echo off
setlocal EnableExtensions
title QuantLab - Full Testnet Diagnostic (Spot + Futures)

call "%~dp0_common.bat" || exit /b 1
set "LOG=%QL_LOG_DIR%\07_full_diagnostic_%QL_STAMP%.log"

echo.
echo ============================================================
echo  QuantLab - 07_full_testnet_diagnostic.bat
echo  Diagnostico dual Spot + Futures (sin ordenes).
echo  Log: %LOG%
echo ============================================================
echo.

%QL_TESTNET_CMD% diagnostic --market all > "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
type "%LOG%"

if not "%RC%"=="0" (
  echo.
  echo [RESULTADO] Ningun mercado READY - ver log arriba.
  echo            Spot: diagnostic --market spot
  echo            Futures: diagnostic --market futures
  exit /b 1
)

echo.
echo [RESULTADO] Al menos un mercado TESTNET READY: YES
exit /b 0
