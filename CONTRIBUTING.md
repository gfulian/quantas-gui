# Contributing to Quantas GUI

Contributions are welcome in the form of code, tests, documentation,
scientific feedback, interface review, and reproducible bug reports.

Quantas GUI is a scientific frontend. Changes must preserve the boundary
between presentation and the Quantas numerical library.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e /path/to/quantas
python -m pip install -e ".[dev,performance]"
python tools/run_checks.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e "C:\path\to\quantas"
python -m pip install -e ".[dev,performance]"
python tools\audit_dash_components.py
python -m pytest -q
```

## Architectural rules

- import scientific functionality only from `quantas.api`;
- never make Quantas depend on Dash, Plotly, browser state, or deployment
  infrastructure;
- do not call Click commands or parse terminal output from the GUI;
- keep numerical arrays, HDF5 files, and active scientific objects server-side;
- keep browser stores limited to identifiers and lightweight interface state;
- preserve raw numerical values and apply rounding only in renderers;
- keep reusable components and renderers general;
- keep unique scientific selection and behaviour in the corresponding module
  adapter or workflow package;
- use replaceable execution, workspace, cache, and result-store contracts;
- preserve responsive behaviour, keyboard focus, and theme compatibility.

## Scientific changes

A renderer or workflow must not silently alter:

- formulas or numerical methods;
- units or tensor conventions;
- array shapes or branch identity;
- masks, tolerances, or interpolation policy;
- stored precision or HDF5 values.

Scientific workflow changes should identify the corresponding public Quantas
contract and include a comparison with API or CLI reference results.

## Testing

Run the standard checks before submitting a pull request:

```bash
python tools/audit_dash_components.py
python tools/run_checks.py
```

Visual changes should be checked in:

- Quantas Dark and Quantas Light;
- standard and large typography;
- desktop and narrow/mobile viewports;
- representative empty, normal, warning, and error states.

Large-result changes should include a performance check and must not transfer
complete numerical payloads into browser storage.

## Pull requests

Keep pull requests focused on one milestone or problem. Describe:

- the user-visible change;
- the architectural layer affected;
- the scientific contract used;
- tests and reference data;
- screenshots for visual changes;
- any compatibility or deployment implications.

The current development sequence is defined in [ROADMAP.md](ROADMAP.md). New
features should normally be associated with the milestone in which their full
workflow is scheduled.
