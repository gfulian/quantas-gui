"""Regression tests for the reproducible code-quality baseline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_quality_tools_are_pinned_in_project_and_constraints() -> None:
    pyproject = _text("pyproject.toml")
    constraints = _text("constraints/quality-baseline.txt")

    for requirement in ("ruff==0.16.0", "mypy==2.3.0"):
        assert f'"{requirement}"' in pyproject
        assert requirement in constraints.splitlines()


def test_ruff_uses_explicit_stable_configuration() -> None:
    pyproject = _text("pyproject.toml")

    assert '[tool.ruff.lint]\nselect = ["E4", "E7", "E9", "F", "I", "UP", "B", "SIM"]' in pyproject
    assert pyproject.count("preview = false") >= 3
    assert "docstring-code-format = false" in pyproject


def test_repository_checks_limit_ruff_to_python_trees() -> None:
    checks = _text("tools/run_checks.py")

    assert 'PYTHON_PATHS = ("src", "tests", "tools")' in checks
    assert '"ruff",\n                "check"' in checks
    assert '"ruff",\n                "format"' in checks
    assert '"ruff", "check", "."' not in checks
    assert '"ruff", "format", "--check", "."' not in checks


def test_ci_installs_all_reproducibility_constraints() -> None:
    workflow = _text(".github/workflows/ci.yml")

    assert "constraints/ui-baseline.txt" in workflow
    assert "constraints/quality-baseline.txt" in workflow
    assert "constraints/backend-baseline.txt" in workflow
    assert "-c constraints/quality-baseline.txt" in workflow
    assert "-c constraints/backend-baseline.txt" in workflow


def test_mypy_skips_third_party_implementation_details() -> None:
    pyproject = _text("pyproject.toml")

    for module_pattern in (
        '"dash"',
        '"dash.*"',
        '"dash_ag_grid"',
        '"plotly"',
        '"plotly.*"',
        '"numpy"',
        '"numpy.*"',
    ):
        assert module_pattern in pyproject
    assert 'follow_imports = "skip"' in pyproject
    assert "follow_imports_for_stubs = true" in pyproject


def test_numpy_runtime_range_is_not_downgraded_for_mypy() -> None:
    pyproject = _text("pyproject.toml")
    constraints = _text("constraints/quality-baseline.txt")

    assert '"numpy>=1.24,<3"' in pyproject
    assert "numpy" not in constraints.lower()


def test_windows_validator_uses_supported_check_arguments() -> None:
    powershell_script = _text("scripts/validate_windows.ps1")
    command_script = _text("scripts/validate_windows.cmd")

    assert "tools\\run_checks.py" in powershell_script
    assert "tools\\run_checks.py" in command_script
    assert "--build" not in powershell_script
    assert "--build" not in command_script
    assert "[dev,performance]" in powershell_script
    assert "[dev,performance]" in command_script
    assert "Invoke-Checked" in powershell_script
    assert "EnableDelayedExpansion" in command_script


def test_windows_command_validator_is_included_in_source_archives() -> None:
    manifest = _text("MANIFEST.in")

    assert "recursive-include scripts *.sh *.ps1 *.cmd" in manifest


def test_runtime_file_lock_dependency_is_declared() -> None:
    pyproject = _text("pyproject.toml")

    assert '"filelock>=3.16,<4"' in pyproject


def test_quantas_is_a_required_constrained_backend() -> None:
    pyproject = _text("pyproject.toml")
    constraints = _text("constraints/backend-baseline.txt")
    workflow = _text(".github/workflows/ci.yml")

    assert '"quantas>=2.0.0b8,<2.1"' in pyproject
    assert "quantas==2.0.0b8" in constraints.splitlines()
    assert "repository: gfulian/quantas" in workflow
    assert "ref: dev/refactor" in workflow
    assert ".ci/quantas" in workflow
    assert "[project.optional-dependencies]\nquantas" not in pyproject


def test_packaging_does_not_advertise_unimplemented_job_backends() -> None:
    pyproject = _text("pyproject.toml").lower()

    for package in ("diskcache", "celery", "redis"):
        assert package not in pyproject
    assert "server = [" in pyproject
    assert "gunicorn" in pyproject
    assert "waitress" in pyproject
