@echo off
setlocal EnableExtensions
title QuantLab - Configure Testnet Credentials

call "%~dp0_common.bat" || exit /b 1
echo.
echo ============================================================
echo  QuantLab - 02_configure_testnet_credentials.bat
echo  Configura .env local (NO se imprimen secretos).
echo  Obtenga keys en: https://testnet.binance.vision
echo ============================================================
echo.

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo Creado .env desde .env.example
  ) else (
    echo.>.env
    echo Creado .env vacio.
  )
)

echo Ingrese credenciales LIVE unlock (QuantLab, no Binance):
set /p "QL_LIVE_USER=QUANTLAB_LIVE_USER: "
set /p "QL_LIVE_PASS=QUANTLAB_LIVE_PASSWORD: "

echo.
echo Ingrese API Key Testnet (visible al tipear; no se mostrara el secret):
set /p "QL_API_KEY=BINANCE_DEMO_API_KEY: "

rem Secret oculto
set "QL_API_SECRET="
for /f "delims=" %%P in ('powershell -NoProfile -Command "$p=Read-Host 'BINANCE_DEMO_API_SECRET' -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))"') do set "QL_API_SECRET=%%P"

if "%QL_LIVE_USER%"=="" (
  echo [ERROR] QUANTLAB_LIVE_USER requerido.
  exit /b 1
)
if "%QL_LIVE_PASS%"=="" (
  echo [ERROR] QUANTLAB_LIVE_PASSWORD requerido.
  exit /b 1
)
if "%QL_API_KEY%"=="" (
  echo [ERROR] BINANCE_DEMO_API_KEY requerido.
  exit /b 1
)
if "%QL_API_SECRET%"=="" (
  echo [ERROR] BINANCE_DEMO_API_SECRET requerido.
  exit /b 1
)

powershell -NoProfile -Command ^
  "$envPath='.env';" ^
  "$lines=Get-Content $envPath -ErrorAction SilentlyContinue;" ^
  "$map=@{}; foreach($l in $lines){ if($l -match '^\s*([^#=]+)=(.*)$'){ $map[$matches[1].Trim()]=$matches[2] } };" ^
  "$map['QUANTLAB_LIVE_USER']='%QL_LIVE_USER%';" ^
  "$map['QUANTLAB_LIVE_PASSWORD']='%QL_LIVE_PASS%';" ^
  "$map['QUANTLAB_DEMO_USE_TESTNET']='1';" ^
  "$map['BINANCE_DEMO_API_KEY']='%QL_API_KEY%';" ^
  "$map['BINANCE_DEMO_API_SECRET']='%QL_API_SECRET%';" ^
  "$out=@(); foreach($k in $map.Keys){ $out += ($k + '=' + $map[$k]) };" ^
  "Set-Content -Path $envPath -Value $out -Encoding UTF8"

set "QL_LIVE_PASS="
set "QL_API_SECRET="

echo.
echo [OK] .env actualizado (secretos no mostrados).
echo Siguiente: 03_test_binance_testnet_connection.bat
exit /b 0
