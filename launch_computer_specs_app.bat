@echo off
setlocal

if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" "%~dp0computer_specs_app.py"
    goto :check_error
)

if exist "%~dp0venv_api\Scripts\python.exe" (
    "%~dp0venv_api\Scripts\python.exe" "%~dp0computer_specs_app.py"
    goto :check_error
)

py -3 "%~dp0computer_specs_app.py"
goto :check_error

:check_error
if errorlevel 1 (
    echo.
    echo L'application s'est fermee avec une erreur.
    pause
)
