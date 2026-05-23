@echo off
REM ============================================================
REM   Fichier : install_dependencies.bat
REM   Projet  : ERP Rosan
REM   Rôle    : Installation automatique des dépendances Windows
REM ============================================================

echo.
echo ============================================================
echo   INSTALLATION DES DEPENDANCES - ERP ROSAN
echo ============================================================
echo.

REM Vérification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH
    echo [INFO] Telechargez Python sur https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detecte
echo.

REM Activation de l'environnement virtuel si existant
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
) else (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo.
echo [INFO] Mise a jour de pip...
python -m pip install --upgrade pip

echo.
echo [INFO] Installation des dependances depuis requirements.txt...
pip install -r backend\requirements.txt

echo.
echo ============================================================
echo   INSTALLATION TERMINEE
echo ============================================================
echo.
echo Pour lancer l'ERP, executez:
echo   start_backend.bat
echo.
echo Ou manuellement:
echo   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
echo.
pause
