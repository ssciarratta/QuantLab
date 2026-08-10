@echo off
setlocal EnableExtensions
title QuantLab Workbench — reinicio tip
cd /d "%~dp0"
echo.
echo Reiniciando QuantLab Workbench (mata :8765 y arranca tip)...
echo.
call "%~dp0tools\windows\_common.bat" || exit /b 1
if exist "scripts\arrancar_workbench.py" (
  "%QL_PY%" scripts\arrancar_workbench.py
) else (
  %QL_WORKBENCH_CMD%
)
exit /b %ERRORLEVEL%
