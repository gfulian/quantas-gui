# Quantas GUI

<p align="center"><img src="src/quantas_gui/assets/quantas-logo.png" alt="Quantas logo" width="120"></p>

<p align="center"><strong>An interactive interface for the Quantas scientific library</strong></p>

[![Quantas GUI CI](https://github.com/gfulian/quantas-gui/actions/workflows/ci.yml/badge.svg)](https://github.com/gfulian/quantas-gui/actions/workflows/ci.yml)
[![Development Status: Alpha](https://img.shields.io/badge/status-alpha-orange)](CHANGELOG.md)
[![Python 3.10+](https://img.shields.io/badge/Python-%3E%3D3.10-blue)](https://www.python.org/downloads/)
[![License: BSD 3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue)](LICENSE)

Quantas GUI is the graphical companion to
[Quantas](https://github.com/gfulian/quantas), a Python library for analysing
solid-state properties. Quantas performs the scientific work; this package
provides the forms, workflow controls, tables and interactive Plotly figures
needed to use that work from a browser.

That separation is deliberate. Numerical methods, physical conventions, units,
precision and native HDF5 persistence remain in Quantas. The GUI talks to the
public `quantas.api` interface and does not call the command-line application or
reach into private backend modules.

The application currently runs like a desktop program: `quantas-gui` starts a
local Dash server and opens the default browser. The same code can also run
behind a WSGI server in a controlled laboratory environment. Public multi-user
deployment will require additional authentication, ownership and resource
management that are not part of the current alpha.

## Where the project stands

The current package is **`0.2.9a4`**, the final hardening stage of the `0.2`
Result Explorer milestone.

The application already includes:

- a responsive shell for desktop, tablet and mobile layouts;
- Quantas Dark, Quantas Light and operating-system theme modes;
- browser-local preferences for text size, motion and table density;
- a Result Explorer for native Quantas `.h5`, `.hdf5` and `.hdf` files;
- compatibility checks for the installed Quantas backend;
- a safe degraded mode when the backend is missing or incompatible;
- lazy report and plot construction through public Quantas lifecycle methods;
- Dash AG Grid tables with raw-value sorting and complete CSV downloads;
- Plotly renderers for Cartesian, contour, polar, surface, spherical and panel
  specifications;
- module-aware presentation for Elasticity, SEISMIC, HA, QHA,
  Thermoelasticity and EOS archives;
- server-side artifact caching, atomic file publication and cross-process
  workspace locks;
- an isolated Scientific UI Kit, started with `quantas-gui --ui-kit`;
- deployment-neutral contracts for future background jobs and result stores.

The GUI does not yet run scientific calculations. The first full workflow will
be Elasticity in version `0.3`.

## Installation from source

Quantas GUI is not yet published on PyPI. It currently requires Quantas
`>=2.0.0b7,<2.1`, so the backend and GUI should be installed in the same virtual
environment.

### Windows

```powershell
git clone https://github.com/gfulian/quantas-gui.git
cd quantas-gui

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e "C:\path\to\quantas"
python -m pip install -e ".[performance]"
```

When a pull or update changes project dependencies, rerun the last two install
commands. This is important for runtime packages such as `filelock`; importing
the source tree is not a substitute for reinstalling the project.

### Linux and macOS

```bash
git clone https://github.com/gfulian/quantas-gui.git
cd quantas-gui

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e /path/to/quantas
python -m pip install -e ".[performance]"
```

The Quantas path must point to the directory containing its `pyproject.toml`.

## Running the application

With the environment active:

```bash
quantas-gui
```

By default the launcher binds to `127.0.0.1`, looks for an available port
starting at `8050`, and opens the browser. Useful options include:

```bash
quantas-gui --no-browser
quantas-gui --port 8060
quantas-gui --debug
quantas-gui --url-prefix /quantas/
quantas-gui --ui-kit
```

The UI Kit is a development tool rather than a normal application page. Its
separate profile uses the same components, themes and settings as the main GUI
without appearing in the scientific navigation.

## Validating a Windows checkout

The recommended command is the batch validator, which is not affected by
PowerShell script-signing policies:

```cmd
scripts\validate_windows.cmd "C:\path\to\quantas"
```

It creates or refreshes `.venv`, installs the backend and all constrained GUI
dependencies, then runs Ruff, mypy, pytest, the Dash component audit, package
builds and `twine check`.

The PowerShell script remains available:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
    .\scripts\validate_windows.ps1 `
    -QuantasPath "C:\path\to\quantas"
```

This changes the execution policy only for that PowerShell process. The project
does not recommend weakening the machine-wide policy.

## Result Explorer

The Result Explorer identifies each native result through
`quantas.api.registry`. It can show:

- provenance, inputs, options, warnings and stored events;
- report tables built by the public module API;
- valid plot families, properties and contexts discovered from public plot
  inventories;
- interactive Plotly figures generated from frontend-neutral PlotSpecs;
- bounded technical information about the stored payload;
- original HDF5 files, reports, tables and supported scientific exports.

Large arrays and open HDF5 objects stay in the controlled server-side
workspace. The browser receives only opaque identifiers and lightweight
interface state.

EOS follows a persistent session model and is therefore different from the
other modules. The generic Explorer offers read-only structural and fit-record
inspection; the complete EOS interface belongs to milestone `0.7`.

## Running on a laboratory server

The WSGI entry point is:

```text
quantas_gui.wsgi:server
```

Install the `server` extra and use Waitress on Windows or Gunicorn on Linux.
All workers must share the configured workspace root. Workspace access is
coordinated across processes, while the current artifact cache remains local to
each worker.

This setup is suitable for a controlled laboratory network. It is not yet a
public service: authentication, per-user ownership, quotas, retention, worker
isolation and a persistent job queue still need to be added.

See [Server deployment](docs/server-deployment.md) for the supported boundary
and configuration examples.

## Documentation

Start with the [documentation index](docs/README.md). The most useful project
references are:

- [Current project state](PROJECT_STATE.md)
- [Roadmap](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [Architectural decisions](ARCHITECTURAL_DECISIONS.md)
- [Result Explorer](docs/results-explorer.md)
- [Execution and concurrency](docs/execution-and-concurrency.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Contributing

Code, tests, documentation, interface review and scientific feedback are all
welcome. Please keep changes focused and preserve the boundary between the GUI
and the public Quantas API. The setup, validation and pull-request process are
explained in [CONTRIBUTING.md](CONTRIBUTING.md).

## License and citation

Quantas GUI is distributed under the BSD 3-Clause license. See
[LICENSE](LICENSE).

Citation metadata is kept in [CITATION.cff](CITATION.cff) and will be completed
as the project approaches its first stable release.
