# Quantas GUI project state

This document is the operational source of truth for the current state of
Quantas GUI. It records the active milestone, validated baseline, completed
work, open issues, and next operation.

It is intentionally concise and current. Historical changes belong in
[CHANGELOG.md](CHANGELOG.md), public release goals belong in
[ROADMAP.md](ROADMAP.md), and durable technical decisions belong in
[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md).

## State metadata

| Item | Current value |
|---|---|
| Last updated | 2026-07-26 |
| Current public milestone | `0.2` — Result Explorer |
| Current development package | `0.2.1a4` |
| Quantas backend baseline | `2.0.0b6`, `dev-refactor` line |
| Legacy reference | Quantas `0.9.1` |
| Repository | `https://github.com/gfulian/quantas-gui` |
| Development status | Alpha |
| Primary runtime mode | Local browser application |
| Next public milestone | `0.3` — Elasticity workflow |

## Canonical source hierarchy

Use project sources in the following order when behaviour or architecture is
unclear:

1. the current Quantas GUI repository or latest approved source snapshot;
2. the current Quantas `dev-refactor` repository;
3. this `PROJECT_STATE.md` file;
4. [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md);
5. the current roadmap, documentation, and tests;
6. Quantas `0.9.1`, only as a legacy behavioural and format reference.

Quantas `0.9.1` must not be used automatically as an architectural model for
Quantas 2 or Quantas GUI.

## Project scope

Quantas is the scientific backend. Quantas GUI is an independent Dash and
Plotly frontend that consumes the public `quantas.api` contract.

The GUI is responsible for:

- application navigation and user interaction;
- scientific input forms and preliminary structural validation;
- workflow orchestration;
- progress, log, warning, and error presentation;
- result inspection, interactive tables, and Plotly figures;
- controlled uploads, downloads, workspaces, and lightweight session state.

Quantas remains responsible for:

- scientific formulas and algorithms;
- physical conventions and units;
- typed scientific input, options, and results;
- numerical validation and calculation;
- native HDF5 persistence;
- frontend-neutral report and plot specifications;
- explicit interoperability transformations.

## Milestone status

| Version | Capability | Status |
|---|---|---|
| `0.1` | Application foundation | Complete |
| `0.2` | Result Explorer | In progress |
| `0.3` | Elasticity workflow | Planned |
| `0.4` | SEISMIC workflow | Planned |
| `0.5` | HA/QHA workflow | Planned |
| `0.6` | Thermoelasticity workflow | Planned |
| `0.7` | EOS workflow | Planned |
| `0.8` | Interoperability | Planned |
| `0.9` | Integration, testing, and beta validation | Planned |
| `1.0` | First stable release and PyPI publication | Planned |

The complete public definition and exit criterion for each milestone are in
[ROADMAP.md](ROADMAP.md).

## Completed foundation

The `0.1` application foundation is considered complete. The repository
contains:

- an installable `quantas-gui` package and `quantas-gui` launcher;
- an application factory, health endpoint, URL-prefix support, and WSGI entry
  point;
- a responsive desktop and mobile application shell;
- Quantas Dark, Quantas Light, and operating-system theme selection;
- configurable typography, reduced motion, and table density;
- a declarative scientific form system and Scientific UI Kit;
- shared feedback components for progress, logs, warnings, errors, and results;
- controlled local workspaces with opaque identifiers and atomic uploads;
- replaceable execution, cache, result-store, and workspace interfaces;
- packaging, CI, cross-platform support files, and Windows PowerShell tooling;
- exact UI dependency baselines for Dash, Dash AG Grid, and Plotly;
- exact code-quality baselines for Ruff and mypy, with an explicit project rule
  set and the Python tree formatted under Ruff `0.16.0`;
- runtime and static audits for the Dash components used by the project.

## Current Result Explorer implementation

The current `0.2.1a4` package includes an alpha Result Explorer with:

- controlled upload of native `.h5`, `.hdf5`, and `.hdf` results;
- result identification through `quantas.api.registry`;
- lightweight overview, provenance, input, options, warning, event, and payload
  inventory views;
- reusable Dash AG Grid table rendering with CSV export;
- Plotly rendering for Cartesian, contour, polar, surface, spherical, summary,
  and panel specifications;
- module-aware result adapters for Elasticity, SEISMIC, HA, QHA, and
  Thermoelasticity;
- structural inspection of EOS archives without treating EOS as a standard
  one-shot result;
- lazy construction of report and plot families;
- bounded server-side artifact caching;
- plot-specific controls for presentation options such as colormap, hover,
  legend, axes, contours, projection, opacity, and camera;
- browser state limited to opaque identifiers and lightweight interface state.

No executable scientific workflow is exposed through the GUI yet.

## Verified evidence

The following evidence has been obtained during development:

- the source package compiles and builds as both wheel and source distribution;
- the application shell, landing page, Settings page, and Scientific UI Kit
  have been exercised in a Windows Dash `4.4.1` environment;
- the Windows runtime baseline has passed `63` pytest tests and all `81` Dash
  component and page audits on the `0.2.1a2` source before the quality-source
  correction;
- the Result Explorer pipeline has been exercised with a native Elasticity
  HDF5 result;
- repeated report and plot-family requests reuse the artifact cache instead of
  rebuilding the scientific collection;
- component compatibility checks cover constructor and callback properties for
  the pinned Dash, Dash AG Grid, and Plotly baseline;
- the `0.2.1a4` source compiles and its available non-browser test suite passes
  in the build environment.

The remaining evidence required for this maintenance checkpoint is a complete
Windows run of Ruff `0.16.0`, mypy `2.3.0`, pytest, the Dash audit, package
build, and `twine check`, followed by a green GitHub Actions matrix.

## Work currently in progress

The active work remains inside milestone `0.2`:

1. validate the directly corrected `0.2.1a4` source with Ruff `0.16.0`, mypy
   `2.3.0`, tests, Dash audits, and package build in the real Windows
   development environment;
2. obtain a fully green GitHub Actions matrix on `main`;
3. review the Result Explorer visualizers separately for Elasticity, SEISMIC,
   HA, QHA, Thermoelasticity, and EOS structure;
4. define the final common Plotly control set and the module-specific plot
   selections;
5. validate tables, figures, units, masks, labels, and exports against
   representative native Quantas results;
6. profile large tables, dense grids, spherical maps, and 3D figures;
7. close the `0.2` milestone only after visual, scientific, responsive, and
   performance validation.

## Immediate next operation

Remove any temporary repair scripts copied into the repository, reinstall the
declared development environment, and run the complete validation baseline on
Windows PowerShell:

```powershell
python -m pip install --upgrade `
    -c constraints\ui-baseline.txt `
    -c constraints\quality-baseline.txt `
    -e ".[dev,performance]"
python tools\run_checks.py
quantas-gui
```

Push the maintenance commit only after all local checks pass, then confirm that
all GitHub Actions matrix jobs are green. After the runtime baseline passes,
inspect representative HDF5 files module by module and record defects or
missing controls before implementing the Elasticity workflow.

## Known limitations and open issues

- the first public CI run remains red at Ruff and mypy; `0.2.1a4` contains the
  direct source corrections, but the final Windows and remote green runs are
  not yet verified;
- module-specific Result Explorer views have not yet received systematic
  scientific sign-off;
- Plotly controls, annotations, comparison modes, export behaviour, and camera
  policies still require module-by-module review;
- performance has been improved through lazy construction and caching, but
  large real datasets still require profiling;
- the local execution backend for scientific workflows is not implemented;
- background jobs, cancellation, recovery, and progress transport are not yet
  connected to executable workflows;
- Redis/Celery or another shared server execution stack has not been selected
  or implemented;
- authentication, quotas, workspace ownership, and public-service security are
  outside the current local milestone;
- EOS remains limited to structural archive inspection in the generic Result
  Explorer;
- the public GitHub repository is populated; its first CI matrix is red at the
  code-quality stages and awaits validation of the `0.2.1a4` direct source
  correction.

## Open decisions

The following items remain deliberately undecided:

- representative validation datasets required to close milestone `0.2`;
- final common and module-specific Plotly controls;
- local background-job implementation;
- shared cache and worker technology for multi-process deployment;
- authentication and result-retention policy for a future public service;
- whether interoperability will remain a guided sequence of explicit actions or
  later justify a more general workflow editor;
- final documentation hosting and release automation for `1.0`.

These items must not be treated as accepted architecture until recorded in
[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md).

## Runtime baseline

The current package declares:

| Dependency | Baseline |
|---|---|
| Python | `>=3.10` |
| Quantas | `>=2.0.0b6,<2.1` when installed through the optional extra |
| Dash | `4.4.1` |
| Dash AG Grid | `35.2.0` |
| Plotly | `6.9.0` |
| NumPy | `>=1.24,<3` |
| Flask | `>=3.1.3,<3.2` |
| Werkzeug | `>=3.1.6,<3.2` |

The exact Dash component properties used by the application must be checked
against this declared baseline rather than assumed from another Dash release.

## Update policy

Update this file whenever one of the following changes:

- current package or backend baseline;
- active milestone or milestone status;
- completed capability;
- known blocking issue;
- verified platform or test evidence;
- next operation;
- source hierarchy.

Do not turn this file into a changelog. Remove resolved operational details and
keep the current state readable in one pass.
