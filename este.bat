@echo off
setlocal EnableExtensions
chcp 65001 >nul
title QuantLab — arrancar con este.bat

cd /d "%~dp0"

echo.
echo  ========================================
echo   ARRANCAR CON ESTE.BAT
echo   QuantLab Workbench + Chat IA
echo  ========================================
echo.

call "%~dp0tools\windows\_common.bat" || (
  echo  [ERROR] No se pudo preparar el entorno.
  pause
  exit /b 1
)

REM Kronos (Alpha Scanner): instala vendor/deps solo si faltan
if defined QL_PY (
  "%QL_PY%" "%QL_ROOT%\scripts\ensure_kronos.py" --quiet
) else (
  where uv >nul 2>&1
  if not errorlevel 1 uv run --no-sync python scripts\ensure_kronos.py --quiet
)

REM Preferir venv local: evita que uv run reescriba quantlab-workbench.exe bloqueado
if defined QL_PY (
  set "PYTHONPATH=%QL_ROOT%\src;%PYTHONPATH%"
  "%QL_PY%" -c "import runpy; runpy.run_path(r'%QL_ROOT%\scripts\arrancar_workbench.py', run_name='__main__')"
  goto :done
)

where uv >nul 2>&1
if not errorlevel 1 (
  uv run --no-sync python scripts\arrancar_workbench.py
  goto :done
)

echo  [ERROR] Falta .venv. Primera vez: uv sync --extra dev
pause
exit /b 1

:done
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo  [ERROR] QuantLab termino con codigo %RC%.
pause
exit /b %RC%
