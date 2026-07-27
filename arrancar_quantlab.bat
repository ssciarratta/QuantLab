@echo off
setlocal EnableExtensions
chcp 65001 >nul
title QuantLab — arrancar

cd /d "%~dp0"

echo.
echo  ========================================
echo   QuantLab Workbench + Chat IA
echo  ========================================
echo.

REM Preferir python del venv; si no, uv
set "PY=%CD%\.venv\Scripts\python.exe"
if exist "%PY%" (
  "%PY%" "%CD%\scripts\arrancar_workbench.py"
) else (
  where uv >nul 2>&1
  if errorlevel 1 (
    echo  [ERROR] Falta .venv. Primera vez:
    echo          uv sync --extra dev
    pause
    exit /b 1
  )
  echo  Primera vez: uv sync --extra dev ...
  uv sync --extra dev
  if errorlevel 1 (
    echo  [ERROR] uv sync fallo.
    pause
    exit /b 1
  )
  uv run python scripts\arrancar_workbench.py
)

echo.
pause
