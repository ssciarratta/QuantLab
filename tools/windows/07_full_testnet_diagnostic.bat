@echo off
setlocal EnableExtensions
title QuantLab - Full Testnet Diagnostic

call "%~dp0_common.bat" || exit /b 1
set "LOG=%QL_LOG_DIR%\07_full_diagnostic_%DATE:~-4%%DATE:~3,2%%DATE:~0,2%.log"

echo.
echo ============================================================
echo  QuantLab - 07_full_testnet_diagnostic.bat
echo  Diagnostico integral TESTNET READY (sin ordenes).
echo  Log: %LOG%
echo ============================================================
echo.

%QL_TESTNET_CMD% diagnostic > "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
type "%LOG%"

if not "%RC%"=="0" (
  echo.
  echo [RESULTADO] TESTNET READY: NO (ver log arriba).
  exit /b 1
)

echo.
echo [RESULTADO] TESTNET READY: YES
exit /b 0
