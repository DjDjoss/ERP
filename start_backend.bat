@echo off
REM Wrapper to run start_backend.ps1 via PowerShell (double-clickable)
pushd %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dp0start_backend.ps1' %*"
if errorlevel 1 (
	echo.
	echo Le backend s'est arrete avec une erreur. Consulte le message ci-dessus.
	pause
)
popd
