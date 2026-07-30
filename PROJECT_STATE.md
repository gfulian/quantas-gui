# Quantas GUI project state

This file is the quickest way to understand where the project is now and what
should happen next. It is intentionally practical: completed work, current
limitations and the next development step belong here. Historical details stay
in [CHANGELOG.md](CHANGELOG.md), longer-term goals in [ROADMAP.md](ROADMAP.md),
and durable technical choices in
[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md).

## Current snapshot

| Item | Current value |
|---|---|
| Last updated | 2026-07-30 |
| Active milestone | `0.2` — Result Explorer |
| Development package | `0.2.9a4` |
| Quantas baseline | `2.0.0b7`, `dev-refactor` line |
| Legacy reference | Quantas `0.9.1` |
| Status | Alpha |
| Main runtime | Local browser application |
| Next milestone | `0.3` — Elasticity workflow |

## Which sources take precedence

When two files disagree, use this order:

1. the newest approved Quantas GUI source snapshot or repository state;
2. the current Quantas `dev-refactor` code and tests;
3. this file;
4. the architectural decisions;
5. the roadmap and other documentation;
6. Quantas `0.9.1`, only for legacy behaviour, formats or numerical comparison.

The legacy package is useful evidence, but it is not a template for the current
architecture.

## Project boundary

Quantas is the scientific backend. It owns calculations, physical conventions,
units, typed inputs and options, numerical results, HDF5 persistence, reports,
plot specifications, events and interoperability.

Quantas GUI is the frontend. It owns forms, navigation, workflow orchestration,
progress and error presentation, AG Grid tables, Plotly rendering, browser
preferences and controlled workspace access.

Runtime scientific integration goes through `quantas.api`. The GUI must not
import the CLI, private calculators, internal module implementations, Rich or
Matplotlib renderers, or HDF5 internals to recreate scientific meaning.

## Milestone overview

| Version | Capability | Status |
|---|---|---|
| `0.1` | Application foundation | Complete |
| `0.2` | Result Explorer | Final hardening |
| `0.3` | Elasticity workflow | Next |
| `0.4` | SEISMIC workflow | Planned |
| `0.5` | HA/QHA workflow | Planned |
| `0.6` | Thermoelasticity workflow | Planned |
| `0.7` | EOS workflow | Planned |
| `0.8` | Interoperability | Planned |
| `0.9` | Integrated beta validation | Planned |
| `1.0` | First stable release | Planned |

## What is already in place

The application foundation includes:

- an installable package and `quantas-gui` launcher;
- an application factory, WSGI entry point, URL-prefix support and health
  endpoints;
- a responsive shell with system, dark and light themes;
- browser-local typography, motion and table-density settings;
- declarative scientific forms and reusable feedback components;
- a separate Scientific UI Kit profile, launched with `quantas-gui --ui-kit`;
- controlled workspaces with opaque identifiers and atomic writes;
- replaceable execution, cache, result-store and workspace contracts;
- pinned Dash, Dash AG Grid, Plotly, Ruff and mypy baselines;
- CI, packaging and cross-platform development tooling.

## Result Explorer status

The `0.2.9a4` Result Explorer uses the Quantas `2.0.0b7` public lifecycle API.
Its current behaviour includes:

- required backend compatibility checks at startup;
- a non-scientific degraded mode when Quantas is missing or incompatible;
- upload blocking before browser data are decoded if the backend is not ready;
- result identification and reopening through `quantas.api.registry`;
- lightweight overview, provenance, input, option, warning and event views;
- report tables built through public module operations;
- scientific plot inventories supplied by Quantas rather than hard-coded in the
  GUI;
- exact property and context selectors derived from those inventories;
- lazy PlotSpec construction with selection-aware cache keys;
- presentation-only controls that reuse cached scientific specifications;
- AG Grid tables with raw numerical values and complete CSV downloads;
- Plotly rendering for Cartesian, contour, polar, surface, spherical, summary
  and panel specifications;
- adapters for Elasticity, SEISMIC, HA, QHA and Thermoelasticity;
- read-only structural and fit-record inspection for EOS archives;
- original-result, report, table and supported scientific downloads;
- an opaque handoff contract that future workflows can use to open their result
  directly in the shared Explorer.

The browser never stores complete results, HDF5 objects or large numerical
arrays.

## Concurrency and file safety

The `0.2.9` hardening work added the safeguards needed before executable
workflows are introduced:

- workspace reads, writes and deletion are coordinated with cross-process file
  locks;
- uploads and exports are published atomically;
- artifact construction is single-flight inside each application process;
- closing a result invalidates its cache namespace;
- an in-flight builder cannot put an artifact back after the result has been
  closed;
- a workspace cannot be removed while another process is still reading it;
- long calculations have a deployment-neutral job, event, progress and
  cancellation contract.

The current execution backend is intentionally disabled because no GUI workflow
exists yet. Elasticity will provide the first process-backed local worker in
`0.3`. A multi-worker server will later need a shared queue and persistent job
store behind the same interface.

## Changes in `0.2.9a4`

This patch closes the complete Windows gate for `0.2.9a3`. Ruff lint and mypy
were already green; the remaining issues were three formatter differences and
a Windows-specific `fsync` failure during atomic export publication. Those
issues are now fixed, and the full local Windows validator passes.

The patch:

- applies the exact Ruff `0.16.0` formatting reported by Windows;
- reopens completed temporary exports with a writable descriptor before calling
  `fsync`, which is required by Windows and leaves the file contents unchanged;
- adds a regression test that fails if atomic publication returns to a
  read-only descriptor;
- documents how GitHub Actions obtains the Quantas backend independently of the
  GUI repository.

## Evidence available now

The following checks have been completed in the review environment:

- Python compilation of `src`, `tests` and `tools`;
- focused tests for cache concurrency, workspace locking, job contracts,
  serialization, public error handling and quality configuration;
- the complete Windows validator passes in the maintainer environment,
  including Ruff lint and formatting, mypy, pytest, the Dash component audit,
  package builds and `twine check`;
- `173` tests pass against the supplied Quantas `2.0.0b7` source and `3`
  Dash-dependent tests are skipped only in the reduced review environment,
  where Dash is unavailable;
- static inspection confirms that runtime scientific integration remains behind
  the public `quantas.api` boundary;
- `filelock` is present as a required runtime dependency in `pyproject.toml`.

## What still needs sign-off before closing `0.2`

1. Confirm the GitHub Actions gate on the same source.
2. Open representative native results for every module.
3. Compare Plotly output with the current Quantas Matplotlib reference where
   equivalent figures exist.
4. Check dark and light themes, keyboard use, disabled states and narrow mobile
   layouts.
5. Profile dense QHA tables, contours, spherical maps and 3D figures.
6. Record any final defects, correct them, and then mark the Result Explorer
   milestone complete.

## Local validation and next operation

The complete local gate is now green. The validator that avoids PowerShell
signing restrictions remains:

```cmd
scripts\validate_windows.cmd "C:\path\to\quantas-dev-refactor"
```

The PowerShell equivalent can still be used with a process-local policy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
    .\scripts\validate_windows.ps1 `
    -QuantasPath "C:\path\to\quantas-dev-refactor"
```

The next operation is to push this source on a development branch, open a pull
request against `main`, and confirm the complete GitHub Actions matrix. The two
application profiles can still be checked manually with:

```powershell
quantas-gui
quantas-gui --ui-kit
```

Then audit representative files with:

```powershell
python tools\audit_result_explorer.py <result-file>
```

## Known limitations

- No scientific workflow can yet be submitted from the GUI.
- The job contract exists, but the local process worker is reserved for `0.3`.
- Artifact caches are process-local, even when workspaces are shared between
  WSGI workers.
- Authentication, user ownership, quotas, retention and public-service
  isolation are not implemented.
- HA, Thermoelasticity and EOS exports remain limited by the selectors exposed
  by the current public backend contract.
- EOS remains a read-only archive view in the generic Explorer.
- Final module-by-module scientific and visual sign-off is still pending.
- The public Elasticity documentation and typed `ElasticityInput` contract need
  to be reconciled regarding optional density metadata before the `0.3` form is
  finalised.

## Decisions still open

The project has deliberately not selected:

- the shared server queue and worker technology;
- a shared artifact cache;
- authentication and account management;
- per-user workspace ownership and retention rules;
- object storage versus a shared filesystem;
- a general visual workflow editor;
- the final documentation and release-hosting stack.

These choices should remain behind the accepted interfaces until the relevant
milestone needs them.

## Updating this file

Update `PROJECT_STATE.md` whenever the active version, backend baseline,
completed capability, blocking issue, verified platform or immediate next step
changes. Remove obsolete operational detail rather than letting this become a
second changelog.
