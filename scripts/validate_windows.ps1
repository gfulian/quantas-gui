param(
    [string]$QuantasPath = "",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating .venv with the active Python interpreter..."
    python -m venv (Join-Path $RepositoryRoot ".venv")
}

if (-not $SkipInstall) {
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -e "$RepositoryRoot[dev,performance]"
    if ($QuantasPath) {
        & $VenvPython -m pip install -e $QuantasPath
    }
}

Push-Location $RepositoryRoot
try {
    & $VenvPython tools\audit_dash_components.py
    & $VenvPython -m pytest -q
    & $VenvPython -c "import quantas_gui; print('Quantas GUI', quantas_gui.__version__)"
}
finally {
    Pop-Location
}
