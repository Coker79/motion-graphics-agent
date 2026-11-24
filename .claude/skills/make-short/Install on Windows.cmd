@echo off
rem Double-click to install make-short and everything it needs (no admin rights). Safe to run again.
if not exist "%~dp0setup\setup-windows.ps1" (
  echo.
  echo  This file has to run from the unzipped make-short folder.
  echo  Close this window, right-click the make-short zip, choose "Extract All...",
  echo  then open the extracted make-short folder and double-click "Install on Windows" again.
  echo.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup\setup-windows.ps1"
if errorlevel 1 (
  echo.
  echo  Setup did not finish. The reason is above; references\windows-troubleshooting.md has the usual fixes.
)
echo.
pause
