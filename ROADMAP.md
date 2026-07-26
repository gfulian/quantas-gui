# Quantas GUI roadmap

This roadmap defines the public development milestones of Quantas GUI from the
initial application foundation to the first stable release.

The milestones are based on complete, user-visible capabilities rather than on
calendar dates. A version is considered complete when its workflow can be used
from input to persisted result, has appropriate tests, and produces scientific
results equivalent to the corresponding Quantas API and command-line workflow.

## Development status

| Version | Milestone | Status |
|---|---|---|
| `0.1` | Application foundation | Complete |
| `0.2` | Result Explorer | **Current development stage** |
| `0.3` | Elasticity workflow | Planned |
| `0.4` | SEISMIC workflow | Planned |
| `0.5` | HA/QHA workflow | Planned |
| `0.6` | Thermoelasticity workflow | Planned |
| `0.7` | EOS workflow | Planned |
| `0.8` | Interoperability | Planned |
| `0.9` | Integration, testing, and beta validation | Planned |
| `1.0` | First stable release | Planned |

Development releases may use additional patch and pre-release identifiers, for
example `0.2.1a1`, while work remains within a milestone.

---

## 0.1 — Application foundation

**Goal:** establish an installable, maintainable Dash application that can grow
from local use to a server deployment without changing the scientific backend.

### Delivered capability

- installable `quantas-gui` Python package and command-line launcher;
- responsive application shell, navigation, landing page, and shared styling;
- local browser launch on a controlled loopback address;
- application factory and WSGI entry point;
- dark, light, and system themes;
- configurable typography, reduced motion, and table density;
- reusable scientific form controls and runtime feedback components;
- controlled local workspaces and opaque browser references;
- replaceable execution, cache, and result-store interfaces;
- cross-platform packaging, tests, CI, and repository support files.

### Completion criterion

The application installs and opens reliably on supported platforms, exposes the
shared user-interface components, and remains independent from private Quantas
implementation details.

---

## 0.2 — Result Explorer

**Goal:** create the common result-inspection layer on which every later
workflow will rely.

### Expected capability

- open and identify native Quantas HDF5 results through `quantas.api`;
- display metadata, provenance, normalized input, options, warnings, and events;
- render frontend-neutral `ReportTable` objects as interactive data grids;
- export unmodified numerical table values to CSV and reports to plain text;
- render Quantas plot specifications with Plotly;
- support line, contour, polar, 3D surface, spherical, summary, and panel plots;
- provide plot-specific controls for colormaps, contours, legends, axes,
  projection, opacity, hover, and camera;
- separate shared rendering logic from module-specific scientific selection;
- construct expensive reports and figures lazily and cache them server-side;
- provide structural inspection of EOS archives without forcing them into the
  standard result model.

### Completion criterion

Representative results from Elasticity, SEISMIC, HA, QHA,
Thermoelasticity, and EOS can be opened and inspected consistently. Tables and
figures are scientifically faithful, responsive, and sufficiently performant
for routine use.

**Current position:** `0.2.1a1` is an alpha implementation of this milestone.
The remaining work is systematic visual, scientific, and performance validation
against representative native result files.

---

## 0.3 — Elasticity workflow

**Goal:** implement the first complete executable workflow using the simplest
scientific module as the reference pattern for later calculators.

### Expected capability

- load or enter an elastic tensor, density, symmetry, and calculation options;
- validate tensor shape, symmetry, units, and required metadata;
- run the Elasticity calculator through `quantas.api`;
- display progress, messages, warnings, errors, and structured results;
- inspect stiffness, compliance, stability, and Voigt–Reuss–Hill properties;
- render directional 2D polar plots and 3D property surfaces with Plotly;
- support tensor rotations and relevant plotting options;
- save native HDF5 results and export supported tables and data products;
- reopen the generated file in the Result Explorer.

### Completion criterion

A complete Elasticity calculation can be performed from the GUI and produces
the same numerical result as the equivalent Quantas API and CLI workflow.

---

## 0.4 — SEISMIC workflow

**Goal:** expose the full Christoffel and seismic-wave analysis through an
interactive workflow.

### Expected capability

- load elastic tensors and density from files, manual input, or compatible
  Quantas results;
- configure angular sampling, physical conventions, tolerances, and output;
- calculate phase and group velocities, polarization, degeneracies,
  enhancement, extrema, and anisotropy;
- inspect standard, extended, and diagnostic reports;
- render 2D maps, spherical projections, polarization overlays, summaries, and
  interactive 3D wave surfaces;
- export native results and supported downstream data products.

### Completion criterion

The GUI reproduces the complete supported SEISMIC workflow and its numerical
results, including interactive inspection of directional and polarization data.

---

## 0.5 — HA/QHA workflow

**Goal:** provide one coherent thermodynamic calculator in which the user
selects harmonic or quasi-harmonic treatment.

### Expected capability

- select **Harmonic Approximation** or **Quasi-Harmonic Approximation** within a
  shared workflow;
- load and inspect supported phonon and volume-dependent input data;
- configure temperature, pressure, fitting, interpolation, and diagnostic
  options appropriate to the selected method;
- preview data coverage and validate required thermodynamic inputs;
- calculate thermodynamic functions in HA mode;
- calculate equilibrium volume and pressure-dependent thermodynamic properties
  in QHA mode;
- display fitting diagnostics, warnings, equation-of-state behaviour, and
  thermodynamic tables;
- render temperature curves, volume-dependent fits, pressure–temperature maps,
  and other supported Plotly views;
- save native HDF5 results and supported exports.

### Completion criterion

Both HA and QHA calculations can be completed through the same calculator while
preserving their distinct scientific options, diagnostics, and result models.

---

## 0.6 — Thermoelasticity workflow

**Goal:** implement the more complex quasi-static thermoelastic workflow by
combining volume-dependent elastic data with thermodynamic results.

### Expected capability

- load elastic-volume series and a compatible QHA result;
- validate composition, volume coverage, units, tensor conventions, and
  pressure–temperature domain compatibility;
- configure calibration, fitting, extrapolation, and analysis options;
- perform Point, Grid, and Profile analyses;
- inspect volume fits, elastic constants, moduli, density, and derived seismic
  properties as functions of pressure and temperature;
- render elastic-volume fits, P–T maps, surfaces, and depth profiles;
- save native results and export valid SEISMIC inputs at selected conditions.

### Completion criterion

The complete supported Thermoelasticity workflow can be executed and inspected
without manually reconstructing intermediate data outside the application.

---

## 0.7 — EOS workflow

**Goal:** provide the dedicated interactive equation-of-state calculator and
archive interface required by the EOS session model.

### Expected capability

- import and edit P–V, V–T, P–V–T, energy–volume, and supported linear data;
- select datasets, exclude or restore observations, and inspect uncertainties;
- configure model, order, solver, weighting, initial values, fixed parameters,
  and bounds;
- support OLS, WLS, and ODR where available in Quantas;
- fit P–V, V–T, and P–V–T models and calculate derived properties;
- compare fit attempts and explicitly accept or reject candidates;
- preserve EOS sessions, diagnostics, covariance, warnings, and accepted records
  in the native archive;
- integrate data, fitted curves, residuals, normalized-pressure diagnostics,
  confidence information, and P–V–T surfaces in the workflow;
- export tables, parameters, diagnostics, and supported data products.

### Completion criterion

EOS fitting and calculation can be performed as a persistent, interactive
session with integrated graphics, rather than as a generic one-shot form.

---

## 0.8 — Interoperability

**Goal:** make the relationships between Quantas modules explicit and usable
without duplicating scientific data entry.

### Expected capability

- pass compatible results between workflows through public Quantas
  interoperability contracts;
- support at least the QHA → Thermoelasticity → SEISMIC chain;
- validate compatibility before a downstream workflow is created;
- preserve provenance, source result identifiers, options, and units;
- allow the user to select the relevant record, pressure, temperature, tensor,
  or analysis context for the next workflow;
- manage related results within a shared local workspace;
- present interoperability as clear scientific actions rather than hidden file
  conversions.

A general visual workflow editor will be considered only if it improves real
scientific use. The first implementation will favour explicit, validated
transitions between known module contracts.

### Completion criterion

A supported multi-module analysis can be completed within Quantas GUI without
manual copying, reformatting, or loss of provenance between stages.

---

## 0.9 — Integration, testing, and beta validation

**Goal:** integrate all workflows into a coherent beta release and validate the
application as a complete scientific frontend.

### Expected capability

- consistent navigation, forms, progress, messages, tables, figures, downloads,
  and error handling across every module;
- end-to-end regression tests for all workflows;
- numerical comparison against Quantas API and CLI reference results;
- validation with representative native datasets and HDF5 files;
- Windows, Linux, and macOS installation and runtime testing;
- performance profiling for large tables, dense grids, and 3D figures;
- accessibility, responsive-layout, and light/dark-theme review;
- local background execution, cancellation, and recovery where required;
- deployment validation with a production WSGI server and replaceable queued
  worker/cache infrastructure;
- complete user documentation, examples, tutorials, and release checklist.

### Completion criterion

Version `0.9` is released as the public beta. All planned workflows are present,
scientifically validated, and suitable for broad user testing. Remaining work
is limited to release-blocking defects, documentation gaps, and final
compatibility hardening.

---

## 1.0 — First stable release

**Goal:** publish the first supported release of Quantas GUI.

### Release requirements

- all `0.9` beta blockers resolved;
- stable application configuration and public integration boundary with
  compatible Quantas releases;
- reproducible builds and signed/tagged release artifacts;
- tested installation on supported Python versions and operating systems;
- complete documentation, examples, citation metadata, and changelog;
- published source distribution and wheel on PyPI;
- documented local use and server deployment procedures;
- no known critical defects affecting scientific correctness, persistence, or
  result provenance.

Version `1.0` will mark the first stable, user-facing release. Later versions
will extend workflows and deployment capabilities without weakening the
separation between Quantas scientific code and the Dash/Plotly frontend.
