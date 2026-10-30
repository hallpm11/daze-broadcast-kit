@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0DazeTelemetry.exe" (
 echo DazeTelemetry.exe not found. Run INSTALL_WINDOWS.cmd from the full Windows release ZIP.
 pause
 exit /b 1
)
start "Daze Telemetry" "%~dp0DazeTelemetry.exe"
exit /b 0
