# Quantas GUI project state

This file is the quickest way to understand what is working today, what has
been validated, and where development should continue. Historical changes are
kept in [CHANGELOG.md](CHANGELOG.md), release goals in
[ROADMAP.md](ROADMAP.md), and long-lived technical decisions in
[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md).

## Current snapshot

| Item | Current value |
|---|---|
| Last updated | 2026-08-02 |
| Latest completed milestone | `0.4` — SEISMIC workflow |
| Development package | `0.4.0a4` |
| Approved SEISMIC baseline | `0.4.0a4` |
| Approved Elasticity baseline | `0.3.0a7` |
| Approved Result Explorer baseline | `0.2.9a4` |
| Next milestone | `0.5` — HA/QHA workflows |
| Quantas baseline | `2.0.0b7` capability snapshot, pending version-label correction to `2.0.0b8` |
| Legacy reference | Quantas `0.9.1` |
| Project status | Alpha |
| Main runtime | Local browser application |

## What is complete

| Version | Capability | Status |
|---|---|---|
| `0.1` | Application foundation | Complete |
| `0.2` | Result Explorer | Complete; baseline `0.2.9a4` |
| `0.3` | Elasticity workflow | Complete; baseline `0.3.0a7` |
| `0.4` | SEISMIC workflow | Complete; baseline `0.4.0a4` |
| `0.5` | HA/QHA workflows | Next |
| `0.6` | Thermoelasticity workflow | Planned |
| `0.7` | EOS workflow | Planned |
| `0.8` | Interoperability | Planned |
| `0.9` | Integrated beta validation | Planned |
| `1.0` | First stable release | Planned |

Quantas remains the scientific backend. It owns formulas, units, numerical
validation, typed inputs and results, events, reports, plot specifications and
native HDF5 persistence. Quantas GUI owns forms, job orchestration, progress and
message presentation, Plotly and AG Grid rendering, downloads and controlled
result handoff. Runtime scientific integration goes through `quantas.api` only.

## SEISMIC milestone summary

The `/seismic` page now supports the full local workflow:

- manual input of job name, density and a complete or triangular stiffness
  matrix;
- controlled import from a shared Quantas input, CRYSTAL output or VASP
  `OUTCAR`;
- upper, lower and full sampling domains;
- phase, group and enhancement calculation levels;
- polarization continuity, public numerical tolerances and physical tensor
  rotation;
- process-backed execution outside Dash HTTP callbacks;
- ordered progress, information, warnings, failures and cooperative
  cancellation;
- atomic native HDF5 publication, deterministic report and sampled CSV export;
- a compact completion summary and direct opening in the Result Explorer.

A non-positive-definite stiffness matrix fails without publishing an apparently
valid result. Density must be finite and positive. The browser stores only
lightweight state and opaque identifiers; scientific arrays and files remain in
the controlled server-side workspace.

## Result Explorer behaviour for SEISMIC

The Result Explorer offers two complementary three-dimensional views:

- **General scalar-field surface** for anisotropy, shear splitting, velocity
  ratios, power-flow angle, enhancement and other sampled scalar fields;
- **Acoustic wave surface** for canonical phase, slowness and group surfaces of
  the P, S1 and S2 modes.

Several scalar properties can be built in one request and switched afterward
without rebuilding the scientific collection. Acoustic surface types and modes
follow the same pattern. The default remains deliberately small so a dense
result does not create a large collection unexpectedly.

## Validation evidence

The complete pinned Windows gate is reported green for `0.4.0a3`, including
Ruff lint, Ruff format, mypy, pytest, the Dash component audit, build and
distribution checks. The closing `0.4.0a4` changes versioning, project status,
workflow-catalogue state and documentation; it does not alter SEISMIC numerical
behaviour.

Scientific and integration validation includes:

- exact preservation of stiffness and density;
- elastic averages and isotropic reference velocities matching a direct public
  API run within `rtol=1e-14`, `atol=1e-14`;
- phase, group and enhancement fields matching within `rtol=1e-12`,
  `atol=1e-12`, including a non-trivial physical tensor rotation;
- monotonic progress and lightweight persisted events;
- controlled failure for a non-positive-definite medium;
- native HDF5 reopening through `quantas.api.seismic.read_result()`;
- sampled CSV generation through the public API;
- automatic opaque handoff to the Result Explorer;
- successful real-data runs from a VASP OHAp output and a CRYSTAL calcite
  output;
- multi-property scalar-surface construction and cache reuse in the Result
  Explorer.

The approved Elasticity evidence remains unchanged: API and CLI equivalence,
HDF5 reopening, warnings for unstable tensors, cancellation, crash cleanup,
concurrent jobs and Android access over a private local network.

## Accepted limitations

- The local process registry is process-local. Closing or refreshing the browser
  does not stop a job, but recovery after restarting the application process is
  not yet claimed.
- Cancellation takes effect at the next public Quantas event or safe
  checkpoint.
- Multi-worker deployment still needs a persistent shared implementation behind
  `ExecutionBackend`.
- Dense 3D figures have limited vertical space on a narrow Android portrait
  viewport but remain usable and display correctly in landscape.
- The backend capability snapshot is still labelled `2.0.0b7`; the planned
  `2.0.0b8` change is a backend version correction and should be recorded when
  it lands.

## Immediate next operation

1. run the closing `0.4.0a4` gate in the pinned Windows environment;
2. commit and push `dev/seismic-0.4`;
3. open and merge the SEISMIC pull request after GitHub Actions are green;
4. keep the branch temporarily as a reference if useful;
5. start milestone `0.5` from the updated `main` branch in a new HA/QHA
   worktree;
6. record the corrected Quantas `2.0.0b8` SHA when the backend version-only
   change is available.
