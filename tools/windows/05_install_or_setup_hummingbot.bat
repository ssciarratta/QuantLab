@echo off
setlocal EnableExtensions
title QuantLab - Install/Setup Hummingbot

call "%~dp0_common.bat" || exit /b 1
echo.
echo ============================================================
echo  QuantLab - 05_install_or_setup_hummingbot.bat
echo  Hummingbot es EXTERNO a QuantLab (Docker/WSL2 recomendado).
echo  Este script NO instala automaticamente; guia al operador.
echo ============================================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
  echo [INFO] Docker no detectado en PATH.
  echo.
  echo Pasos manuales recomendados (Windows):
  echo   1. Instalar WSL2 + Ubuntu: wsl --install -d Ubuntu
  echo   2. Instalar Docker Desktop con integracion WSL2
  echo   3. En Ubuntu/WSL: git clone https://github.com/hummingbot/hummingbot
  echo   4. Seguir README oficial: make setup / docker compose
  echo.
  echo Documentacion: docs/ops/HUMMINGBOT_TESTNET.md
  exit /b 2
)

echo Docker detectado. Comprobando contenedor hummingbot...
docker ps --format "{{.Names}}" | findstr /I "hummingbot hbot" >nul 2>&1
if errorlevel 1 (
  echo [INFO] No hay contenedor Hummingbot corriendo.
  echo.
  echo Para levantar Hummingbot (ejemplo):
  echo   docker pull hummingbot/hummingbot:latest
  echo   docker run -it --name hummingbot -v %%CD%%\hummingbot_files:/home/hummingbot/conf hummingbot/hummingbot:latest
  echo.
  echo Spot testnet en HB: usar binance_paper_trade (no existe binance_testnet spot).
  echo Testnet spot nativo: QuantLab F102 (este proyecto).
  exit /b 2
)

echo [OK] Contenedor Hummingbot detectado.
%QL_TESTNET_CMD% hummingbot
exit /b 0
