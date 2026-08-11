@echo off
setlocal EnableExtensions
chcp 65001 >nul
title QuantLab — ir a entorno prueba UI

set "WT=%~dp0..\QuantLab-ui-redesign"
if not exist "%WT%\cambio entorno prueba.bat" (
  echo  [ERROR] No se encuentra el worktree UI:
  echo          %WT%
  echo  Clona o crea QuantLab-ui-redesign junto a QuantLab.
  pause
  exit /b 1
)

cd /d "%WT%"
call "%WT%\cambio entorno prueba.bat"
exit /b %ERRORLEVEL%
