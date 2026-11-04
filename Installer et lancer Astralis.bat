@echo off
setlocal
cd /d "%~dp0"
title Astralis - installation et demarrage
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Installer et lancer Astralis.ps1"
if errorlevel 1 (
  echo.
  echo Une erreur est survenue au demarrage. Copie le message ci-dessus.
  pause
)
endlocal
