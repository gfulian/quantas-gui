# Quantas GUI roadmap

This roadmap follows usable scientific capabilities rather than calendar dates.
A milestone is complete only when the feature works from input to persisted
result, has suitable tests and documentation, and agrees numerically with the
corresponding Quantas API and command-line workflow.

Alpha releases may add patch and pre-release identifiers while a milestone is
still being completed, for example `0.2.9a4`.

## Milestones at a glance

| Version | Main capability | Status |
|---|---|---|
| `0.1` | Application foundation | Complete |
| `0.2` | Result Explorer | Complete |
| `0.3` | Elasticity workflow | Complete |
| `0.4` | SEISMIC workflow | Complete |
| `0.5` | HA/QHA workflow | Current |
| `0.6` | Thermoelasticity workflow | Planned |
| `0.7` | EOS workflow | Planned |
| `0.8` | Interoperability | Planned |
| `0.9` | Integrated beta validation | Planned |
| `1.0` | First stable release | Planned |

---

## 0.1 — Application foundation

The first milestone established a package that could grow without tying the
scientific code to Dash or to a particular deployment model.

It delivered:

- the installable `quantas-gui` package and launcher;
- an application factory and WSGI entry point;
- responsive desktop and mobile navigation;
- dark, light and operating-system themes;
- browser-local appearance settings;
- reusable scientific controls and declarative form schemas;
- progress, log, warning, error and result components;
- controlled local workspaces;
- replaceable execution, cache, result-store and workspace interfaces;
- packaging, CI and cross-platform development tools;
- an isolated Scientific UI Kit for component development.

**Status:** complete.

---

## 0.2 — Result Explorer

The Result Explorer is the common destination for every Quantas result,
regardless of whether it was uploaded by the user or produced by a future GUI
workflow.

The milestone includes:

- controlled upload of native Quantas HDF5 files;
- backend compatibility diagnostics and degraded startup;
- result identification through the public registry;
- overview, provenance, inputs, options, warnings and events;
- public report tables rendered with Dash AG Grid;
- complete table and report downloads;
- public plot inventories and explicit scientific selectors;
- lazy PlotSpec construction and server-side caching;
- Plotly rendering for all currently exposed specification families;
- module-aware presentation for Elasticity, SEISMIC, HA, QHA and
  Thermoelasticity;
- read-only structural and fit-record inspection for EOS archives;
- safe concurrent access, atomic publication and controlled close behaviour;
- an opaque result handoff for future workflows.

The milestone is complete when representative results from every module can be
opened, inspected and exported reliably, with scientifically faithful figures,
acceptable performance and verified behaviour on supported platforms and
viewports.

**Status:** complete. `0.2.9a4` is the approved Result Explorer baseline and
remains available on its dedicated maintenance branch while later workflow
milestones continue independently.

---

## 0.3 — Elasticity workflow

Elasticity is the first complete executable workflow and the reference
implementation for later calculators.

The completed workflow allows the user to:

- load a shared Quantas input, import CRYSTAL or VASP output, or paste a full or
  triangular elastic stiffness tensor;
- edit the job name and canonical 6 × 6 stiffness matrix in GPa;
- configure the public 2D, 3D and physical tensor-rotation options that are
  meaningful in the GUI;
- rely on Quantas for crystal-system inference and final scientific validation;
- submit the calculation to a separate local process rather than an HTTP
  callback;
- follow ordered events, progress, warnings, failures and cooperative
  cancellation;
- inspect a compact report-based summary without duplicating the Result
  Explorer;
- download the native HDF5 result and deterministic report;
- open the completed result directly in the shared Result Explorer.

The form follows the typed public backend contract. Elasticity intentionally
ignores density metadata from the input convention shared with SEISMIC and does
not expose manual symmetry or false plotting and unit controls.

**Status:** complete. `0.3.0a7` is the approved Elasticity baseline. The full
Windows quality gate is green, API and CLI numerical equivalence are covered,
native HDF5 reopening and opaque Result Explorer handoff are verified, and the
workflow has been exercised from an Android browser over a private local
network.

**Completion evidence:** stiffness is preserved exactly; compliance and
Voigt–Reuss–Hill values agree with the direct API and CLI within
`rtol=1e-14`, `atol=1e-14`; persisted directional arrays agree within
`rtol=1e-12`, `atol=1e-12`. Stable, unstable, invalid, cancelled, crashed and
concurrent-job paths are covered.

---

## 0.4 — SEISMIC workflow

SEISMIC brings Christoffel-equation analysis into the same complete application
lifecycle established by Elasticity, while adding density, spherical sampling
and wave-mode diagnostics.

The completed workflow allows the user to:

- enter or import a job name, elastic stiffness tensor and density;
- load the shared Quantas input format or extract compatible data from CRYSTAL
  and VASP outputs through the public backend API;
- configure upper, lower or full angular domains and phase, group or enhancement
  calculation levels;
- preserve polarization continuity, public tolerances and physical tensor
  rotations;
- run the calculation in a separate local process with progress, ordered
  messages, cancellation and controlled failure states;
- download the native HDF5 result, deterministic report and sampled CSV;
- inspect a compact result summary and open the completed result directly in the
  shared Result Explorer.

The Result Explorer distinguishes **General scalar-field surfaces** from
canonical **Acoustic wave surfaces**. Several scalar properties, surface types
or acoustic modes can be built together and switched afterward without
rebuilding the collection.

**Status:** complete. `0.4.0a4` is the approved SEISMIC baseline. The pinned
Windows quality gate is green, real CRYSTAL and VASP inputs have been exercised,
native HDF5 reopening and result handoff are verified, and phase, group and
enhancement fields agree with the direct public API.

**Completion evidence:** stiffness and density are preserved exactly; elastic
averages and isotropic reference velocities agree within `rtol=1e-14`,
`atol=1e-14`; sampled phase, group and enhancement fields agree within
`rtol=1e-12`, `atol=1e-12`. Invalid density, non-positive-definite media,
cancellation, progress, CSV export and cache reuse are covered.

---

## 0.5 — HA/QHA workflow

HA and QHA will share one calculator where that improves the user experience,
while keeping their scientific options and results distinct.

The milestone will cover:

- selection of Harmonic or Quasi-Harmonic treatment;
- supported phonon and volume-dependent inputs;
- temperature and pressure domains;
- fitting, interpolation, uncertainty and diagnostic options;
- thermodynamic functions in HA mode;
- equilibrium volume and pressure-dependent properties in QHA mode;
- fitting diagnostics, warnings and equation-of-state behaviour;
- temperature curves, volume fits, pressure–temperature maps and slices;
- native HDF5 results and supported exports.

**Completion test:** both modes can be completed from the GUI and reproduce the
corresponding backend workflows.

---

## 0.6 — Thermoelasticity workflow

Thermoelasticity combines volume-dependent elastic data with a compatible QHA
result and therefore exercises the interoperability and long-job architecture
more heavily.

The workflow will provide:

- elastic-volume series and QHA result selection;
- checks for composition, volume coverage, units and P–T domain compatibility;
- calibration, fitting, quality, uncertainty and extrapolation options;
- Point, Grid and Profile analyses;
- elastic constants, moduli, density and derived seismic properties across
  pressure and temperature;
- fit diagnostics, P–T maps, surfaces and depth profiles;
- native persistence and valid SEISMIC input export.

**Completion test:** the supported quasi-static workflow can be performed
without reconstructing intermediate data outside the application.

---

## 0.7 — EOS workflow

EOS needs a dedicated interface because it is a persistent fitting session, not
a simple one-input/one-result calculation.

The milestone will include:

- import and editing of supported P–V, V–T, P–V–T, energy–volume and linear
  datasets;
- observation inclusion and exclusion;
- model, order, solver, weighting, initial-value, fixed-parameter and bound
  controls;
- OLS, WLS and ODR where supported by Quantas;
- fit attempts, diagnostics and derived-property calculations;
- explicit acceptance or rejection of candidate fits;
- archive history, covariance, warnings and accepted records;
- data, fit, residual, normalized-pressure and P–V–T surface views;
- tables, parameters, diagnostics and supported exports.

**Completion test:** an EOS analysis can be resumed and managed as a persistent
session without forcing it into the generic workflow model.

---

## 0.8 — Interoperability

This milestone will make supported relationships between modules visible and
safe to use.

The first target is the chain:

```text
QHA → Thermoelasticity → SEISMIC
```

The GUI will:

- use public Quantas interoperability operations;
- check compatibility before creating a downstream workflow;
- preserve provenance, units, source identifiers and selected records;
- let the user choose the relevant pressure, temperature, tensor or analysis
  context;
- keep related results within a controlled workspace;
- present clear scientific actions rather than hidden file conversions.

A general node editor will be considered only if explicit, validated transitions
prove too limiting for real use.

**Completion test:** a supported multi-module analysis can be completed without
manual copying, reformatting or loss of provenance.

---

## 0.9 — Integrated beta validation

Version `0.9` brings the separate workflows together and tests the application
as one scientific product.

The beta milestone requires:

- consistent forms, progress, messages, tables, figures and downloads;
- end-to-end tests for every workflow;
- numerical comparison with API and CLI references;
- representative native datasets and HDF5 files;
- Windows, Linux and macOS installation and runtime checks;
- performance profiling for large tables, grids and 3D figures;
- accessibility, responsive layout and theme review;
- background execution, cancellation and recovery where required;
- production WSGI validation and replaceable shared worker/cache services;
- complete user and developer documentation.

**Completion test:** all planned workflows are present and scientifically
validated, with only release-blocking defects and final documentation work left.

---

## 1.0 — First stable release

The first stable release will be published only after the beta blockers are
closed.

Release requirements include:

- a stable configuration and public integration boundary with supported Quantas
  versions;
- reproducible wheel and source builds;
- tested installation on supported Python versions and operating systems;
- complete documentation, examples, citation metadata and changelog;
- publication on PyPI;
- documented local and server deployment procedures;
- no known critical defect affecting scientific correctness, persistence or
  provenance.

Later releases may expand workflows and deployment options, but they should not
weaken the separation between the Quantas scientific backend and the Dash/Plotly
frontend.
