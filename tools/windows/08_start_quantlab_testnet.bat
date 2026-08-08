@echo off
setlocal EnableExtensions
title QuantLab - Start Workbench (Testnet mode)

call "%~dp0_common.bat" || exit /b 1
echo.
echo ============================================================
echo  QuantLab - 08_start_quantlab_testnet.bat
echo  Valida TESTNET READY y arranca Workbench (sin ordenes).
echo ============================================================
echo.

echo [1/2] Diagnostico previo...
call "%~dp0_common.bat" >nul 2>&1
%QL_TESTNET_CMD% diagnostic --skip-network
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo [WARN] Diagnostico local indica problemas. Ejecute 07_full_testnet_diagnostic.bat
  echo        Si desea continuar de todos modos, presione una tecla...
  pause >nul
)

echo [2/2] Iniciando Workbench en http://127.0.0.1:8765 ...
echo LIVE_BLOCKED permanece True. Testnet remoto requiere unlock + flag en .env
echo.

%QL_WORKBENCH_CMD%
exit /b %ERRORLEVEL%
