param(
    [string]$QuantasPath = "",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
$UiConstraints = Join-Path $RepositoryRoot "constraints\ui-baseline.txt"
$QualityConstraints = Join-Path $RepositoryRoot "constraints\quality-baseline.txt"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating .venv with the active Python interpreter..."
    python -m venv (Join-Path $RepositoryRoot ".venv")
}

if (-not $SkipInstall) {
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install `
        -c $UiConstraints `
        -c $QualityConstraints `
        -e "${RepositoryRoot}[dev,performance]"
    if ($QuantasPath) {
        & $VenvPython -m pip install -e $QuantasPath
    }
}

Push-Location $RepositoryRoot
try {
    & $VenvPython tools\run_checks.py
    & $VenvPython -c "import quantas_gui; print('Quantas GUI', quantas_gui.__version__)"
}
finally {
    Pop-Location
}
