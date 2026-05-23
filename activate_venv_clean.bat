@echo off
set "VIRTUAL_ENV_DISABLE_PROMPT=1"
call .\venv_api\Scripts\activate

:: Premier nettoyage
cls

:: On laisse VS Code afficher son bruit
ping 127.0.0.1 -n 2 > nul

:: Deuxième nettoyage (celui que tu faisais manuellement)
cls

:: Prompt final propre
echo (venv_api) E:\ERP_Rosan>
