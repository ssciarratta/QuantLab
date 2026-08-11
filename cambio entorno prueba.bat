@echo off
setlocal EnableExtensions
chcp 65001 >nul
title QuantLab — arranque con smoke UI

cd /d "%~dp0"

echo.
echo  ========================================================
echo   QUANTLAB — Smoke UI + Workbench
echo   Rama main ^| UI friendly + Monte Carlo + SLT
echo  ========================================================
echo.

set "PY=%CD%\.venv\Scripts\python.exe"

where uv >nul 2>&1
if errorlevel 1 (
  echo  [ERROR] Falta uv en PATH.
  pause
  exit /b 1
)

if not exist "%PY%" (
  echo  Primera vez: uv sync --extra dev ...
  uv sync --extra dev
  if errorlevel 1 (
    echo  [ERROR] uv sync fallo.
    pause
    exit /b 1
  )
)

echo  [1/2] Smoke test UI ...
echo.
call "%~dp0scripts\smoke_ui_redesign.bat"
if errorlevel 1 (
  echo.
  echo  [ERROR] Smoke test fallo.
  pause
  exit /b 1
)
echo.

echo  [2/2] Arrancando Workbench en http://127.0.0.1:8765 ...
echo.

if exist "%PY%" (
  "%PY%" "%CD%\scripts\arrancar_workbench.py"
) else (
  uv run python scripts\arrancar_workbench.py
)

set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo  [ERROR] Termino con codigo %RC%.
pause
exit /b %RC%
