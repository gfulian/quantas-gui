# Contributing to Quantas GUI

Code, tests, documentation, scientific review and reproducible bug reports are
welcome. Quantas GUI is a scientific frontend, so every change must preserve
the boundary with Quantas and leave formulas, units, precision and native
persistence in the backend.

## Preparing the environment

On Windows, the recommended path is:

```powershell
.\scripts\validate_windows.cmd "C:\path\to\quantas"
```

The command creates `.venv`, reinstalls the declared dependencies and runs the
complete gate. The PowerShell version can be invoked with a process-local
policy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
    .\scripts\validate_windows.ps1 `
    -QuantasPath "C:\path\to\quantas"
```

On Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e /path/to/quantas
python -m pip install -c constraints/ui-baseline.txt \
    -c constraints/quality-baseline.txt \
    -c constraints/backend-baseline.txt -e ".[dev,performance]"
python tools/run_checks.py
```

When `pyproject.toml` changes, reinstall the project. An editable checkout does
not add new runtime dependencies automatically.

## Reproducible tool baseline

The exact Ruff and mypy versions are listed in
`constraints/quality-baseline.txt`. Tool upgrades should be focused maintenance
changes that update configuration, source, tests and changelog together.

Ruff checks only `src`, `tests` and `tools`; Markdown prose is reviewed as
documentation rather than formatted as Python.

## Architectural rules

- Use only the public `quantas.api` surface for scientific work.
- Do not import the CLI, internal modules, Rich or Matplotlib into the GUI.
- Keep large arrays, HDF5 files and scientific objects server-side.
- Store only identifiers and lightweight state in the browser.
- Round values in renderers, never in the underlying data.
- Keep shared components and services genuinely generic.
- Put module-specific scientific choices in the module adapter.
- Depend on replaceable job, workspace, cache and result contracts.
- Check themes, keyboard use, disabled states and narrow viewports.

## Scientific changes

The GUI must not alter formulas, units, tensor conventions, array shapes,
masks, tolerances or stored precision. A workflow change should name the public
Quantas contract it uses and compare results with an API or CLI reference.

Plotly changes follow
[docs/plotly-fidelity.md](docs/plotly-fidelity.md) and are compared with the
Matplotlib rendering of the same public specification.

## Tests and visual review

Before opening a pull request, run:

```bash
python tools/run_checks.py
```

Visual changes should be reviewed in Quantas Dark and Light, on desktop and
mobile, and in empty, normal, warning and error states. Changes affecting large
results also need a performance check.

## Pull requests

Work on a short-lived branch and open a pull request into `main`. Describe the
visible behaviour, architectural layer, scientific contract, tests and any
compatibility or deployment effects.

Merge after the `CI gate`, preferably with squash. Update `CHANGELOG.md` and
`PROJECT_STATE.md` whenever the change alters the real project state.
