param(
    [switch]$MockPappers,
    [string]$ApiHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoReload,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Import-LocalEnv {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            $name = $parts[0].Trim()
            $value = $parts[1].Trim().Trim('"').Trim("'")
            if (-not [Environment]::GetEnvironmentVariable($name, "Process")) {
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}

function Test-PythonModule {
    param(
        [string]$PythonExe,
        [string]$ModuleName
    )

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        return $false
    }

    & $PythonExe -c "import $ModuleName" *> $null
    return $LASTEXITCODE -eq 0
}

function Test-PythonModules {
    param(
        [string]$PythonExe,
        [string[]]$ModuleNames
    )

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        return $false
    }

    $imports = ($ModuleNames | ForEach-Object { "import $_" }) -join "; "
    & $PythonExe -c $imports *> $null
    return $LASTEXITCODE -eq 0
}

function Resolve-PythonWithModules {
    param([string[]]$ModuleNames)

    $candidates = @(
        $env:ERP_BACKEND_PYTHON,
        $env:BACKEND_PYTHON,
        (Join-Path $projectRoot ".venv\Scripts\python.exe"),
        (Join-Path $projectRoot "venv_api\Scripts\python.exe"),
        (Join-Path $projectRoot ".venv-1\Scripts\python.exe")
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-PythonModules -PythonExe $candidate -ModuleNames $ModuleNames) {
            return $candidate
        }

        Write-Warning "Python ignore (dependances manquantes ou Python invalide): $candidate"
    }

    $required = $ModuleNames -join ", "
    $repairPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
    $requirements = Join-Path $projectRoot "requirements.txt"
    throw "Aucun environnement Python backend valide n'a ete trouve. Modules requis: $required. Reparation: `"$repairPython`" -m pip install -r `"$requirements`""
}

function Repair-ProjectEnv {
    $venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
    $requirements = Join-Path $projectRoot "requirements.txt"

    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host "Creation de l'environnement .venv..."
        & py -3 -m venv (Join-Path $projectRoot ".venv") *> $null
        if ($LASTEXITCODE -ne 0) {
            & python -m venv (Join-Path $projectRoot ".venv") *> $null
        }
    }

    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Impossible de creer .venv automatiquement. Verifie que Python est installe."
    }

    Write-Host "Installation / mise a jour des dependances depuis requirements.txt..."
    & $venvPython -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        throw "La reparation automatique a echoue pendant pip install."
    }
}

Import-LocalEnv -Path (Join-Path $projectRoot ".env.local")
$requiredModules = @("uvicorn", "fastapi", "sqlalchemy", "psycopg2", "pydantic", "reportlab", "pandas", "openpyxl")

try {
    $pythonExe = Resolve-PythonWithModules -ModuleNames $requiredModules
} catch {
    Write-Warning $_.Exception.Message
    Write-Host "Tentative de reparation automatique..."
    Repair-ProjectEnv
    $pythonExe = Resolve-PythonWithModules -ModuleNames $requiredModules
}

if ($MockPappers) {
    $env:PAPPERS_MOCK_MODE = "1"
    Write-Host "Mode mock Pappers activé (PAPPERS_MOCK_MODE=1)."
} else {
    Remove-Item Env:PAPPERS_MOCK_MODE -ErrorAction SilentlyContinue
}

$args = @("-m", "uvicorn", "backend.main:app", "--host", $ApiHost, "--port", "$Port")
if (-not $NoReload) {
    $args += "--reload"
}

$cmdPreview = "$pythonExe " + ($args -join " ")
Write-Host "Commande: $cmdPreview"

if ($DryRun) {
    Write-Host "DryRun: aucune exécution."
    exit 0
}

Set-Location -LiteralPath $projectRoot
& $pythonExe @args
