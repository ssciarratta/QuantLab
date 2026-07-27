@echo off
setlocal EnableExtensions
chcp 65001 >nul
title QuantLab — configurar Chat IA

cd /d "%~dp0"

set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%CD%\scripts\configurar_chat_llm.py"
echo.
pause
