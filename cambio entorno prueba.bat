@echo off
setlocal EnableExtensions
chcp 65001 >nul
title QuantLab — CAMBIO ENTORNO PRUEBA (UI redesign)

cd /d "%~dp0"

echo.
echo  ========================================================
echo   CAMBIO ENTORNO PRUEBA
echo   Worktree UI redesign ^| rama feature/ui-radical-simplification
echo   Repo: QuantLab-ui-redesign
echo  ========================================================
echo.
echo  Este entorno NO es el QuantLab principal (este.bat).
echo  Boot: solo ventana Inicio ^| menu por tareas ^| headers ES
echo.

set "PY=%CD%\.venv\Scripts\python.exe"

where uv >nul 2>&1
if errorlevel 1 (
  echo  [ERROR] Falta uv en PATH. Instalalo o usa el venv del repo principal.
  pause
  exit /b 1
)

if not exist "%PY%" (
  echo  Primera vez en este worktree: uv sync --extra dev ...
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
  echo  [ERROR] Smoke test fallo. Revisa arriba antes de arrancar.
  pause
  exit /b 1
)
echo.

echo  [2/2] Arrancando Workbench entorno prueba en http://127.0.0.1:8765 ...
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
