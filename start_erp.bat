@echo off
REM ============================================================================
REM  LANCE L'ERP COMPLET AVEC DETECTION PYTHON + REPARATION AUTOMATIQUE
REM  (GUI PySide6 + backend FastAPI/Uvicorn + orchestrateur)
REM ============================================================================

setlocal EnableExtensions EnableDelayedExpansion

pushd %~dp0

REM ---------------------------------------------------------------------------
REM Charger les variables locales utiles (ex: POSTGRES_PASSWORD)
REM ---------------------------------------------------------------------------
if exist .env.local (
    for /f "usebackq tokens=1* delims==" %%A in (`findstr /b /i "POSTGRES_PASSWORD=" .env.local`) do (
        if not defined POSTGRES_PASSWORD set "POSTGRES_PASSWORD=%%B"
    )
)

if defined POSTGRES_PASSWORD (
    set "PGPASSWORD=%POSTGRES_PASSWORD%"
)

REM ---------------------------------------------------------------------------
REM Variables internes
REM ---------------------------------------------------------------------------
set "PYTHON_EXE="
set "REQUIRED_IMPORTS=import PySide6; import uvicorn; import fastapi; import sqlalchemy"

REM A la base: on tente le venv projet, sinon un python systeme, sinon repair_env
call :find_python

if not defined PYTHON_EXE (
    echo Environnement Python incomplet ou absent. Tentative de reparation automatique...
    call :repair_env
    call :find_python
)

if not defined PYTHON_EXE (
    echo.
    echo Reparation automatique impossible.
    echo Modules requis: PySide6, uvicorn, fastapi, sqlalchemy.
    echo.
    echo Verifie que Python est installe et que la connexion internet fonctionne,
    echo puis relance ce fichier.
    pause
    popd
    exit /b 1
)

REM ---------------------------------------------------------------------------
REM Lancer l'ERP (main.py = orchestrateur + backend + PostgreSQL)
REM ---------------------------------------------------------------------------
"%PYTHON_EXE%" main.py
if errorlevel 1 (
    echo.
    echo L'ERP s'est arrete avec une erreur. Consulte le message ci-dessus.
    pause
)

popd
exit /b %errorlevel%


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:find_python
REM Recherche d'un Python valide en testant les imports requis.
REM Ne depend pas de variables utilisateur (ex: ERP_PYTHON).
set "PYTHON_EXE="

REM 1) Priorite: venv du projet
if exist "%~dp0venv\Scripts\python.exe" (
    call :test_python "%~dp0venv\Scripts\python.exe"
)
if not defined PYTHON_EXE if exist "%~dp0venv_api\Scripts\python.exe" (
    call :test_python "%~dp0venv_api\Scripts\python.exe"
)

REM 2) venv legacy eventuel
if not defined PYTHON_EXE if exist "%~dp0venv-1\Scripts\python.exe" (
    call :test_python "%~dp0venv-1\Scripts\python.exe"
)

REM 3) Sinon: python systeme (Python* sous LocalAppData / ProgramFiles)
if not defined PYTHON_EXE (
    call :find_system_python
)

exit /b 0


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:test_python
REM %1 = chemin python.exe
set "_CAND=%~1"
if exist "%_CAND%" (
    "%_CAND%" -c "%REQUIRED_IMPORTS%" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=%_CAND%"
    )
)
exit /b 0


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:find_system_python
REM Cherche un python systeme et le valide via imports.
set "_CAND="

for %%P in (
    "C:\Users\Bur\AppData\Local\Programs\Python\Python314"
    "C:\Users\Djoss\AppData\Local\Programs\Python\Python314"
    "%LocalAppData%\Programs\Python\Python*"
    "%ProgramFiles%\Python*"
    "%ProgramFiles(x86)%\Python*"
) do (
    if not defined PYTHON_EXE if exist "%%~P\python.exe" (
        call :test_python "%%~P\python.exe"
    )
)


exit /b 0


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:repair_env
REM Creation/réparation de venv + installation requirements.
REM Objectif: garantir un pip valide et tester les imports après install.
set "REPAIR_PYTHON="

REM Choisir le premier python systeme disponible
for %%P in (
    "C:\Users\Bur\AppData\Local\Programs\Python\Python314"
    "C:\Users\Djoss\AppData\Local\Programs\Python\Python314"
    "%LocalAppData%\Programs\Python\Python*"
    "%ProgramFiles%\Python*"
    "%ProgramFiles(x86)%\Python*"
    "%LocalAppData%\Microsoft\WindowsApps\python.exe"
    "%ProgramFiles%\WindowsApps\python.exe"
) do (
    if not defined REPAIR_PYTHON if exist "%%~P" (
        REM %%P peut etre soit un dossier python, soit directement python.exe
        if /I "%%~P"=="%LocalAppData%\Microsoft\WindowsApps\python.exe" (
            set "REPAIR_PYTHON=%%~P"
        ) else (
            if exist "%%~P\python.exe" set "REPAIR_PYTHON=%%~P\python.exe"
        )
    )
)


if not defined REPAIR_PYTHON (
    echo Aucun Python systeme trouve pour creer .venv.
    exit /b 1
)

REM Creer .venv si absent
if not exist "%~dp0venv\Scripts\python.exe" (
    echo Creation de l'environnement .venv...
    "%REPAIR_PYTHON%" -m venv "%~dp0venv"
)

REM Pip: essaye d'abord le module pip, sinon fallback get-pip.
set "_VENV_PY=%~dp0venv\Scripts\python.exe"

echo Initialisation pip dans le venv...
"%_VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    echo pip introuvable dans le venv, tentative avec get-pip.py...
    "%REPAIR_PYTHON%" -c "import sys,urllib.request; print('download get-pip'); urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py','get-pip.py')" >nul 2>nul
    "%_VENV_PY%" get-pip.py >nul 2>nul
    del /q get-pip.py >nul 2>nul
) else (
    "%_VENV_PY%" -m pip install --upgrade pip >nul 2>nul
)

REM Installer / mettre a jour les dependances
echo Installation / mise a jour des dependances depuis requirements.txt...
"%_VENV_PY%" -m pip install -r "%~dp0requirements.txt"

REM Re-test imports requis avec le venv
"%~dp0venv\Scripts\python.exe" -c "%REQUIRED_IMPORTS%" >nul 2>nul
if errorlevel 1 (
    echo Les imports requis echouent meme apres installation.
    echo Verifie requirements.txt et l'environnement.
    exit /b 1
)

exit /b 0

