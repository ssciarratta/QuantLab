@echo off
setlocal EnableExtensions
title QuantLab - Configure Futures Testnet Credentials

call "%~dp0_common.bat" || exit /b 1
echo.
echo ============================================================
echo  QuantLab - 02b_configure_futures_testnet_credentials.bat
echo  Configura Futures USD-M Testnet en .env (NO imprime secretos).
echo  Keys: https://testnet.binancefuture.com
echo  Nota: desactiva Spot remoto si lo tenias activo (solo uno).
echo ============================================================
echo.

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo Creado .env desde .env.example
  ) else (
    echo.>.env
  )
)

echo Ingrese credenciales LIVE unlock (QuantLab, no Binance):
set /p "QL_LIVE_USER=QUANTLAB_LIVE_USER: "
set /p "QL_LIVE_PASS=QUANTLAB_LIVE_PASSWORD: "

echo.
echo Ingrese API Key Futures Testnet:
set /p "QL_API_KEY=BINANCE_FUTURES_DEMO_API_KEY: "

set "QL_API_SECRET="
for /f "delims=" %%P in ('powershell -NoProfile -Command "$p=Read-Host 'BINANCE_FUTURES_DEMO_API_SECRET' -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))"') do set "QL_API_SECRET=%%P"

if "%QL_LIVE_USER%"=="" (
  echo [ERROR] QUANTLAB_LIVE_USER requerido.
  exit /b 1
)
if "%QL_LIVE_PASS%"=="" (
  echo [ERROR] QUANTLAB_LIVE_PASSWORD requerido.
  exit /b 1
)
if "%QL_API_KEY%"=="" (
  echo [ERROR] BINANCE_FUTURES_DEMO_API_KEY requerido.
  exit /b 1
)
if "%QL_API_SECRET%"=="" (
  echo [ERROR] BINANCE_FUTURES_DEMO_API_SECRET requerido.
  exit /b 1
)

powershell -NoProfile -Command ^
  "$envPath='.env';" ^
  "$lines=Get-Content $envPath -ErrorAction SilentlyContinue;" ^
  "$map=@{}; foreach($l in $lines){ if($l -match '^\s*([^#=]+)=(.*)$'){ $map[$matches[1].Trim()]=$matches[2] } };" ^
  "$map['QUANTLAB_LIVE_USER']='%QL_LIVE_USER%';" ^
  "$map['QUANTLAB_LIVE_PASSWORD']='%QL_LIVE_PASS%';" ^
  "$map['QUANTLAB_DEMO_USE_FUTURES_TESTNET']='1';" ^
  "$map['BINANCE_FUTURES_DEMO_API_KEY']='%QL_API_KEY%';" ^
  "$map['BINANCE_FUTURES_DEMO_API_SECRET']='%QL_API_SECRET%';" ^
  "$map['QUANTLAB_DEMO_USE_TESTNET']='0';" ^
  "$out=@(); foreach($k in $map.Keys){ $out += ($k + '=' + $map[$k]) };" ^
  "Set-Content -Path $envPath -Value $out -Encoding UTF8"

set "QL_LIVE_PASS="
set "QL_API_SECRET="

echo.
echo [OK] .env Futures Testnet actualizado. Spot remoto forzado a 0.
echo Siguiente: quantlab-testnet diagnostic --market futures
exit /b 0
