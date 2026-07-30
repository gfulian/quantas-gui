param(
    [string]$QuantasPath = "",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
$UiConstraints = Join-Path $RepositoryRoot "constraints\ui-baseline.txt"
$QualityConstraints = Join-Path $RepositoryRoot "constraints\quality-baseline.txt"
$BackendConstraints = Join-Path $RepositoryRoot "constraints\backend-baseline.txt"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Program,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE: $Program $($Arguments -join ' ')"
    }
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating .venv with the active Python interpreter..."
    Invoke-Checked python -m venv (Join-Path $RepositoryRoot ".venv")
}

if (-not $SkipInstall) {
    Invoke-Checked $VenvPython -m pip install --upgrade pip

    if ($QuantasPath) {
        Invoke-Checked $VenvPython -m pip install -e $QuantasPath
    }

    Invoke-Checked $VenvPython -m pip install `
        -c $UiConstraints `
        -c $QualityConstraints `
        -c $BackendConstraints `
        -e "${RepositoryRoot}[dev,performance]"
}

Push-Location $RepositoryRoot
try {
    Invoke-Checked $VenvPython tools\run_checks.py
    Invoke-Checked $VenvPython -c "import quantas_gui; print('Quantas GUI', quantas_gui.__version__)"
}
finally {
    Pop-Location
}

Write-Host "Validation completed successfully."
