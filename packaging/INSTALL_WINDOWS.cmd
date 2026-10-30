@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL_WINDOWS.ps1"
if errorlevel 1 (
  echo.
  echo INSTALL FAILED. See the message above.
  pause
  exit /b 1
)
echo.
pause
