# Elasticity workflow

**Approved baseline:** Quantas GUI `0.2.9a4`
**Current implementation:** Quantas GUI `0.3.0a5`
**Backend:** Quantas `2.0.0b7`, `dev-refactor` line
**Updated:** 2026-07-31

## Scope

Elasticity is the first executable scientific workflow in Quantas GUI. It is
the reference implementation for later one-shot workflows while preserving the
separation between Quantas and the graphical frontend.

Quantas owns tensor validation, symmetry inference, stability, averages,
directional properties, events, reports and native HDF5. Quantas GUI owns
controlled input, background orchestration, job state, accessible feedback,
summary rendering, downloads and Result Explorer handoff.

Runtime scientific integration uses only `quantas.api.elasticity` and the public
registry. The GUI does not import the CLI, `quantas.modules`, private readers,
Rich or Matplotlib.

## Public contract used

The workflow uses the public typed contracts and operations:

- `Input`, `Options`, `SurfaceOptions`, `TensorRotation`;
- `read_input()`, `normalize_input()`, `run()` and `get_result()`;
- `read_result()` and `write_result()`;
- `build_report()` and `quantas.api.rendering.render_tables()`;
- `create_input()` for CRYSTAL and VASP source conversion.

The public input contains job name, a 6 × 6 stiffness matrix in GPa and optional
source provenance. Crystal symmetry is inferred by Quantas.

### Shared density convention

The generated text format can be shared by Elasticity and SEISMIC and may carry
density metadata. Elasticity intentionally reads only job name and stiffness;
SEISMIC also consumes density. The GUI therefore accepts a shared input with a
density line but never exposes density in the Elasticity form or request.

## Input page

The page converges four source paths into two editable canonical fields:

1. job name;
2. Voigt stiffness matrix in GPa, normalized by the GUI to a full 6 × 6 matrix.

Supported source modes are:

- direct paste;
- Quantas text input, which populates job name and stiffness;
- CRYSTAL output, which populates stiffness through `create_input()`;
- VASP `OUTCAR`, including an extensionless filename, which populates stiffness
  through `create_input()`.

Direct paste accepts four structural representations:

- a complete 6 × 6 matrix;
- a compact upper triangle with row lengths `6, 5, 4, 3, 2, 1`;
- a compact lower triangle with row lengths `1, 2, 3, 4, 5, 6`;
- a 6 × 6 triangular matrix whose omitted strict triangle is padded with zeros.

Unambiguous triangular representations are mirrored into the canonical full
matrix before the public Quantas input is built. A complete matrix with values
in both triangles is never averaged or silently corrected; Quantas retains final
responsibility for scientific symmetry validation.

Uploads are decoded once, bounded, written atomically below a controlled
workspace and parsed server-side. External outputs do not replace an existing
GUI job name. Every imported value remains editable.

Selecting a non-manual mode requires a matching successful upload. Changing the
mode cannot silently reuse provenance from a different source. Manual paste
submits copied values without retaining an unused imported workspace.

## Scientific options

The form exposes only public choices that affect calculated or stored data:

- 2D principal-plane data and angular points;
- 3D directional surfaces, polar and azimuthal sampling;
- selected Young, compressibility, shear and Poisson surface families;
- optional physical XYZ or 3 × 3 tensor transformation.

GPa is displayed as the fixed supported stiffness unit rather than as a false
single-choice selector. CLI/Matplotlib options such as plot, colormap, geometry,
DPI, terminal verbosity and output paths are absent.

`batch_size` is not a user-facing scientific option. The GUI chooses a bounded
internal value from the 3D grid size so that Quantas emits useful progress for
longer calculations while preserving the same numerical operation and stored
values.

## Execution state machine

A Dash callback never performs the scientific calculation. Submit persists the
request and immediately returns a `JobHandle` from the replaceable
`ExecutionBackend`.

The visible states are:

```text
Input
  ↓
Queued → Running → Cancelling
  ↓          ↓
Succeeded   Failed / Cancelled
```

The browser stores only opaque workspace, job and result identifiers, the event
cursor and lightweight presentation state. Requests, uploaded files, events,
logs, reports and HDF5 results stay server-side.

The local backend uses a separate `spawn` process, atomic status files, ordered
JSONL events, cooperative cancellation and atomic final publication. Server
mode displays execution as unavailable until a shared queue-backed backend is
injected.

## Progress, information, warnings and errors

The running view shows:

- job state and current phase;
- monotonic bounded progress or an indeterminate state when no percentage is
  justified;
- current/total counters when Quantas supplies them;
- a cancellation action;
- bounded activity tabs: All, Info, Warnings and Errors.

Icons are accompanied by text labels and are not the only carrier of meaning.
Frequent events remain server-side; at most 500 lightweight records are retained
in browser session state.

A mechanically unstable tensor is a successful scientific result with warnings,
not an infrastructure failure. The summary states that the tensor is unstable
and Quantas omits directional fields that cannot be calculated safely.

A failed worker or scientific exception publishes no valid result. The page
shows an explicit failure banner, a sanitised public message, Back to input and
a diagnostic-log download. Cancelled jobs are reported only after safe cleanup
has been confirmed.

## Result summary and handoff

Successful jobs display a compact workflow summary built from the same public
`ReportTable` objects used by the Result Explorer. The page highlights:

- job name;
- inferred crystal system;
- mechanical stability;
- warning count;
- Voigt-Reuss-Hill averages;
- stability and directional-extrema tables when available.

The complete public report remains expandable, while detailed exploration,
Plotly figures and scientific exports belong to the Result Explorer.

The final actions are:

- Download HDF5;
- Download report;
- Open in Result Explorer;
- Back to input.

The worker embeds a deterministic report in the native HDF5 before atomic
publication. The Explorer handoff registers the existing controlled result and
writes only `ActiveResultState` to the global browser session before navigating
to `/results`.

## Validation evidence

The review environment reports:

```text
202 passed, 4 skipped
```

The skips require the unavailable pinned Dash runtime. Covered evidence
includes:

- shared Quantas input with density metadata;
- public CRYSTAL and VASP input generation;
- source/mode validation and manual-paste provenance;
- compact and zero-padded upper/lower triangular matrix expansion;
- preservation of full asymmetric matrices for Quantas scientific validation;
- process/direct API equality, including physical rotation;
- exact stiffness preservation;
- compliance and VRH equality at `rtol=1e-14`, `atol=1e-14`;
- directional and stored surface equality at `rtol=1e-12`, `atol=1e-12`;
- deterministic HDF5 report text and successful reopening;
- unstable-tensor success with warnings and no directional data;
- ordered cursors, monotonic progress, cancellation, hard crashes, sanitised
  errors and concurrent jobs;
- a real equivalent CLI calculation with the same numerical tolerances.

## Remaining gate

The real Windows worktree must still run Ruff, Ruff format, mypy, pytest, the
Dash component audit, wheel/source build and Twine checks with the pinned UI
stack. Manual acceptance must cover dark, light and system themes; desktop and
narrow mobile viewports; keyboard focus; disabled controls; source imports;
large-grid progress; warnings; failures; cancellation; downloads and Result
Explorer reopening.

```powershell
Set-Location C:\Users\gianf\Desktop\quantas\worktrees\quantas-gui-dev-0.3
.\scripts\validate_windows.ps1 -QuantasPath ..\quantas-dev-refactor
```
