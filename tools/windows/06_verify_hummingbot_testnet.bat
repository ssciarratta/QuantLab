@echo off
setlocal EnableExtensions
title QuantLab - Verify Hummingbot Testnet Safety

call "%~dp0_common.bat" || exit /b 1
echo.
echo ============================================================
echo  QuantLab - 06_verify_hummingbot_testnet.bat
echo  Verifica que configs HB no apunten a produccion spot.
echo ============================================================
echo.

%QL_TESTNET_CMD% hb-verify
set "RC=%ERRORLEVEL%"
%QL_TESTNET_CMD% hummingbot

if not "%RC%"=="0" (
  echo.
  echo [ERROR] Se detectaron posibles referencias a produccion en configs HB.
  exit /b 1
)

echo.
echo [OK] Verificacion HB completada.
exit /b 0
