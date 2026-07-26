"""Run the repository validation stages in isolated subprocesses."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, command: Sequence[str]) -> bool:
    """Run one validation stage and print a stable status line."""
    print(f"\n== {label} ==")
    completed = subprocess.run(command, cwd=ROOT, check=False)
    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"[{status}] {label}")
    return completed.returncode == 0


def main(argv: list[str] | None = None) -> int:
    """Execute linting, typing, tests, and package validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args(argv)

    stages: list[tuple[str, list[str]]] = [
        ("Ruff lint", [sys.executable, "-m", "ruff", "check", "."]),
        ("Ruff format", [sys.executable, "-m", "ruff", "format", "--check", "."]),
        ("mypy", [sys.executable, "-m", "mypy"]),
        ("pytest", [sys.executable, "-m", "pytest", "-q"]),
        (
            "Dash component runtime audit",
            [sys.executable, "tools/audit_dash_components.py"],
        ),
    ]

    results = [run(label, command) for label, command in stages]

    if not args.skip_build:
        build_ok = run("build", [sys.executable, "-m", "build"])
        results.append(build_ok)
        distributions = sorted(str(path) for path in (ROOT / "dist").glob("*"))
        if build_ok and distributions:
            results.append(
                run(
                    "twine check",
                    [sys.executable, "-m", "twine", "check", *distributions],
                )
            )
        else:
            print("[FAIL] twine check: no distributions were produced")
            results.append(False)

    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
