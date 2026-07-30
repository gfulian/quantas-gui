@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPOSITORY_ROOT=%~dp0.."
for %%I in ("%REPOSITORY_ROOT%") do set "REPOSITORY_ROOT=%%~fI"
set "VENV_PYTHON=%REPOSITORY_ROOT%\.venv\Scripts\python.exe"
set "UI_CONSTRAINTS=%REPOSITORY_ROOT%\constraints\ui-baseline.txt"
set "QUALITY_CONSTRAINTS=%REPOSITORY_ROOT%\constraints\quality-baseline.txt"
set "BACKEND_CONSTRAINTS=%REPOSITORY_ROOT%\constraints\backend-baseline.txt"
set "QUANTAS_PATH=%~1"
set "SKIP_INSTALL=0"

if /I "%~1"=="--skip-install" (
    set "SKIP_INSTALL=1"
    set "QUANTAS_PATH="
)
if /I "%~2"=="--skip-install" set "SKIP_INSTALL=1"

if not exist "%VENV_PYTHON%" (
    echo Creating .venv with the active Python interpreter...
    python -m venv "%REPOSITORY_ROOT%\.venv"
    if errorlevel 1 goto :fail
)

if "%SKIP_INSTALL%"=="0" (
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :fail

    if not "%QUANTAS_PATH%"=="" (
        "%VENV_PYTHON%" -m pip install -e "%QUANTAS_PATH%"
        if errorlevel 1 goto :fail
    )

    "%VENV_PYTHON%" -m pip install ^
        -c "%UI_CONSTRAINTS%" ^
        -c "%QUALITY_CONSTRAINTS%" ^
        -c "%BACKEND_CONSTRAINTS%" ^
        -e "%REPOSITORY_ROOT%[dev,performance]"
    if errorlevel 1 goto :fail
)

pushd "%REPOSITORY_ROOT%"
"%VENV_PYTHON%" tools\run_checks.py
set "CHECK_RESULT=%ERRORLEVEL%"
if not "%CHECK_RESULT%"=="0" goto :checks_failed
"%VENV_PYTHON%" -c "import quantas_gui; print('Quantas GUI', quantas_gui.__version__)"
set "CHECK_RESULT=!ERRORLEVEL!"
popd

if not "%CHECK_RESULT%"=="0" exit /b %CHECK_RESULT%
echo Validation completed successfully.
exit /b 0

:checks_failed
popd
exit /b %CHECK_RESULT%

:fail
echo Validation stopped because a setup command failed.
exit /b 1
