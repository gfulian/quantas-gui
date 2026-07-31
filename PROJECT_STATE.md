# Quantas GUI project state

This file is the quickest way to understand where the project is now and what
should happen next. Historical details stay in [CHANGELOG.md](CHANGELOG.md),
longer-term goals in [ROADMAP.md](ROADMAP.md), and durable technical choices in
[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md).

## Current snapshot

| Item | Current value |
|---|---|
| Last updated | 2026-07-31 |
| Completed milestone | `0.3` — Elasticity workflow |
| Development package | `0.3.0a7` |
| Approved Elasticity baseline | `0.3.0a7` |
| Approved Result Explorer baseline | `0.2.9a4` |
| Next milestone | `0.4` — SEISMIC workflow |
| Quantas baseline | `2.0.0b7`, `dev-refactor` line |
| Backend snapshot commit | `e195ac04a40de20607b348be051f37cd7cdb7366` |
| Legacy reference | Quantas `0.9.1` |
| Status | Alpha |
| Main runtime | Local browser application |

## Source and responsibility hierarchy

Use the newest approved GUI source, then current Quantas code and tests, then
this file, accepted architectural decisions and the roadmap. Quantas `0.9.1`
is only a legacy behavioural and format reference.

Quantas owns scientific methods, units, typed contracts, numerical validation,
events and native HDF5 persistence. Quantas GUI owns forms, orchestration, job
presentation, Plotly, AG Grid and opaque result handoff. Runtime scientific
integration uses `quantas.api`, never the CLI or private backend modules.

## Milestone overview

| Version | Capability | Status |
|---|---|---|
| `0.1` | Application foundation | Complete |
| `0.2` | Result Explorer | Complete; baseline `0.2.9a4` |
| `0.3` | Elasticity workflow | Complete; baseline `0.3.0a7` |
| `0.4` | SEISMIC workflow | Next |
| `0.5` | HA/QHA workflow | Planned |
| `0.6` | Thermoelasticity workflow | Planned |
| `0.7` | EOS workflow | Planned |
| `0.8` | Interoperability | Planned |
| `0.9` | Integrated beta validation | Planned |
| `1.0` | First stable release | Planned |

## Branch verification

The supplied GUI archives do not contain `.git` metadata or an embedded GUI
commit SHA. Content and package version can be audited, but ancestry and branch
state must be checked in the Windows worktree before the closing commit:

```powershell
Set-Location C:\Users\gianf\Desktop\quantas\worktrees\quantas-gui-dev-0.3
if ((git branch --show-current) -ne "dev/elasticity-0.3") {
    throw "Wrong GUI branch"
}
git merge-base --is-ancestor <approved-0.2.9a4-commit> HEAD
if ($LASTEXITCODE -ne 0) {
    throw "dev/elasticity-0.3 is not based on 0.2.9a4"
}
```

The dedicated `0.2` worktree remains unchanged.

## Completed Elasticity capability

### Input and scientific contract

The `/elasticity` page accepts:

- editable job name and stiffness matrix in GPa;
- complete 6 × 6 matrices;
- compact upper or lower triangular matrices;
- 6 × 6 triangular matrices padded with structural zeros;
- shared Quantas text input;
- CRYSTAL output;
- extensionless VASP `OUTCAR`;
- public 2D and 3D sampling options;
- selected 3D properties;
- public physical XYZ or 3 × 3 tensor transformations.

Elasticity consumes only job name and stiffness from the input convention shared
with SEISMIC. It does not expose density, manual crystal symmetry, plotting
settings, terminal options or unsupported unit selection.

Triangular paste is expanded structurally before request construction. A full
matrix with populated opposing triangles is preserved exactly rather than
silently averaged; Quantas remains responsible for final scientific validation.

### Execution, feedback and persistence

The workflow includes:

- replaceable local process-backed execution using the portable `spawn`
  context;
- persistent queued, running, cancelling, succeeded, failed and cancelled
  states;
- cursor-based ordered events and bounded monotonic progress;
- current/total counters when emitted by Quantas;
- cooperative cancellation, worker-crash reconciliation and partial-output
  cleanup;
- server-side requests, events, logs and native HDF5 results;
- atomic HDF5 publication and deterministic embedded report;
- explicit success, success-with-warning, failure and cancellation
  presentations;
- report, HDF5 and diagnostic-log downloads;
- opaque registration and automatic opening in the Result Explorer.

Detailed tables and interactive figures remain in the Result Explorer.

### Workflow catalogue

The `/workflows` page is now operational rather than a placeholder. It reports
separately:

- public Quantas API readiness;
- GUI workflow availability;
- principal input;
- canonical persisted result;
- roadmap milestone.

Only Elasticity exposes **Start workflow**. SEISMIC is identified as the next
milestone, while later modules remain clearly marked as planned. The catalogue
does not generate scientific forms mechanically from registry metadata.

## Validation evidence

The complete Windows gate is reported green after the final `0.3.0a6`
formatting correction, including Ruff lint, Ruff format, mypy, pytest, Dash
component audit, build and distribution checks. The final Windows pytest run
reports `218 passed`.

Against Quantas `2.0.0b7`:

- process output and direct API output preserve stiffness exactly;
- compliance and Voigt–Reuss–Hill arrays agree with `rtol=1e-14`,
  `atol=1e-14`;
- directional extrema and persisted 2D/3D arrays agree with `rtol=1e-12`,
  `atol=1e-12`;
- the real CLI workflow matches the direct public API within the same
  tolerances;
- physical tensor rotation, crystal-system inference and stability agree;
- a mechanically unstable tensor succeeds with warnings and no fabricated
  directional fields;
- invalid input, cancellation, hard worker exit, sanitised errors, event
  cursors, process recreation and concurrent jobs are covered;
- HDF5 output reopens through `quantas.api.elasticity.read_result()`;
- Result Explorer handoff opens the registered result rather than requesting a
  new upload;
- the executable workflow and Result Explorer were exercised from an Android
  browser over a private local network.

## Accepted limitations

- The local process registry is intentionally process-local. Browser refresh or
  closure does not stop a job, but application-process restart recovery is not
  claimed.
- Cancellation latency depends on the next public Quantas event or explicit safe
  checkpoint; no deeper kernel cancellation token exists yet.
- Multi-worker server execution needs a persistent shared implementation behind
  `ExecutionBackend`.
- The 3D plot is vertically constrained on a narrow Android portrait viewport,
  but remains usable and displays correctly in landscape. This is accepted as a
  minor non-blocking responsive limitation.

## Immediate next operation

1. apply `0.3.0a7` in the real `dev/elasticity-0.3` worktree;
2. run the complete Windows gate once more;
3. commit, push and confirm GitHub Actions;
4. retain `0.3.0a7` as the approved Elasticity baseline;
5. in the dedicated backend/API chat, prepare the public SEISMIC input-generation
   contract and the separately planned Elasticity additions;
6. create `dev/seismic-0.4` from the approved GUI baseline only after that public
   contract is ready.
