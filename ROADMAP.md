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
| `0.2` | Result Explorer | Current, final hardening |
| `0.3` | Elasticity workflow | Next |
| `0.4` | SEISMIC workflow | Planned |
| `0.5` | HA/QHA workflow | Planned |
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

**Current position:** `0.2.9a4` contains the final code-quality and Windows
validation corrections after the first `0.2.9a2` run. The remaining work is the
full pinned Windows and CI gate, followed by final module-by-module visual,
scientific, accessibility and performance sign-off.

---

## 0.3 — Elasticity workflow

Elasticity will be the first complete executable workflow and the reference
implementation for later calculators.

The workflow will allow the user to:

- load or enter an elastic stiffness tensor and job information;
- configure the options exposed by `quantas.api.elasticity`;
- validate matrix shape, units and cross-field requirements;
- see the elastic symmetry inferred by Quantas;
- submit the calculation to a background process rather than an HTTP callback;
- follow progress, logs, warnings and errors;
- inspect stiffness, compliance, stability and Voigt–Reuss–Hill properties;
- render supported 2D polar and 3D directional views;
- apply physical tensor rotations only through the public Quantas contract;
- save the native HDF5 result;
- open the completed result directly in the shared Result Explorer.

The form will follow the typed public backend contract. Density or manually
selected symmetry will not be added merely because older text mentions them;
those fields must first be supported consistently by Quantas.

**Completion test:** the GUI result must match the equivalent Quantas API and
CLI calculation within the documented numerical tolerances.

---

## 0.4 — SEISMIC workflow

This milestone will expose the Christoffel and seismic-wave analysis as an
interactive workflow.

Planned capabilities include:

- loading elastic tensors and density from files, manual input or compatible
  Quantas results;
- configuring angular sampling, calculation level, tolerances and output;
- phase and group velocities, polarizations, degeneracies, enhancement,
  extrema and anisotropy;
- standard, extended and diagnostic reports;
- 2D maps, spherical projections, polarization overlays, summaries and 3D wave
  surfaces;
- native persistence and supported downstream exports.

**Completion test:** all supported numerical and directional results agree with
the public SEISMIC API and CLI workflow.

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
