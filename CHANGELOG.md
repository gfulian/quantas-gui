# Changelog

All notable changes to Quantas GUI will be documented in this file.

The project follows Semantic Versioning while the public interface remains under
active alpha development.

## 0.2.1a5 — 2026-07-27

Cross-version mypy correction for NumPy stubs in the GitHub Actions matrix.

### Fixed

- enabled `follow_imports_for_stubs` so the existing `follow_imports = "skip"`
  overrides also apply to installed `.pyi` files;
- prevented mypy, configured for the supported Python 3.10 target, from parsing
  NumPy 2.5+ aliases that use Python 3.12 `type`-statement syntax;
- retained `numpy>=1.24,<3`, Python 3.10 compatibility, and full checking of the
  Quantas GUI source tree.

### Validation status

- Ruff, pytest, Dash runtime audits, package build, and metadata checks were
  already green on Python 3.13 across Linux, macOS, and Windows;
- this release isolates the remaining failure to the documented mypy stub-import
  policy and requires one concluding CI matrix run.

## 0.2.1a4 — 2026-07-27

Final source-quality cleanup before the initial consolidated GitHub commit.

### Fixed

- applied the two remaining Ruff `0.16.0` formatting changes;
- added explicit `NDArray` annotations for spherical-map grids, scalar
  backgrounds, and boolean masks required by mypy `2.3.0`;
- removed the obsolete `dash_table.DataTable` compatibility probe because the
  application uses Dash AG Grid exclusively;
- made repository validation remove stale `build/` and `dist/` products before
  creating and checking release artifacts.

### Validation status

- the preceding Windows run confirmed Ruff lint, pytest, the full Dash runtime
  audit, build, and `twine check`;
- this release contains the final Ruff-format and mypy corrections and requires
  one concluding Windows and GitHub Actions run.

## 0.2.1a3 — 2026-07-26

Source-quality correction for the Ruff `0.16.0` and mypy `2.3.0` baseline.

### Changed

- formatted the complete Python source, test, and tool trees with the declared
  Ruff formatter rather than relying on a post-install repair script;
- organized imports and updated annotations for the enabled Ruff `I` and `UP`
  rules;
- retained the supported runtime range `numpy>=1.24,<3` and excluded NumPy's
  implementation stubs from the Python 3.10 mypy target instead of downgrading
  the runtime dependency;
- made `Settings.with_overrides()` explicitly typed rather than forwarding an
  untyped dictionary to `dataclasses.replace()`;
- corrected the Windows validation script to call the supported
  `tools/run_checks.py` interface.

### Fixed

- replaced silent result-cleanup handlers with `contextlib.suppress` as required
  by `SIM105`;
- removed an unused upload-path assignment and simplified the boolean form
  adapter for the enabled Ruff rules;
- validated empty matrix cells before numeric coercion;
- corrected numeric validation variable types and range-triplet issue
  flattening for mypy;
- allowed structured Dash component identifiers in the shared action-button
  contract;
- removed the invalid top-level import pattern from the Dash application tests;
- added regression coverage for the NumPy typing boundary and empty matrix
  cells.

### Validation status

- source compilation and the available non-browser test suite pass in the build
  environment;
- the final Ruff, mypy, Dash runtime, build, and `twine` checks must be rerun in
  the Windows development environment and confirmed by GitHub Actions.

## 0.2.1a2 — 2026-07-26

Initial code-quality baseline introduced after the first public CI run.

### Added

- exact development baselines for Ruff `0.16.0` and mypy `2.3.0`;
- `constraints/quality-baseline.txt` and CI installation through both quality
  and UI constraints;
- regression tests for the declared quality configuration.

### Changed

- made the Ruff rule selection explicit and limited repository checks to the
  Python source, test, and tool trees;
- enabled GitHub annotation output for Ruff in CI;
- included the canonical project-state and architectural-decision documents in
  source distributions.

### Known issue

The baseline configuration was committed before the complete source tree had
been reformatted and before all resulting mypy errors had been corrected. That
incomplete maintenance step is superseded by `0.2.1a3`.

## 0.2.1a1 — 2026-07-26

First repository-ready alpha for the public `gfulian/quantas-gui` project.

### Added

- browser-local **Settings** page;
- Quantas Dark, Quantas Light, and operating-system theme selection;
- compact, standard, comfortable, and large typography scales;
- reduced-motion and table-density preferences;
- local browser persistence that never modifies Quantas inputs or HDF5 files;
- theme synchronization for the application shell, Dash AG Grid, and Result
  Explorer Plotly figures;
- direct Settings access from the sidebar, top bar, and responsive navigation;
- Windows and GitHub Desktop bootstrap instructions for the existing remote
  repository.

### Changed

- rewrote the repository README as a concise introduction, installation, and
  current-status guide;
- replaced the internal incremental roadmap with capability milestones from
  `0.1` through the stable `1.0` release;
- expanded CONTRIBUTING with development, architecture, scientific, testing,
  and pull-request guidance;
- rewrote the landing-page copy in a technical, scientific style;
- removed fabricated recent-workspace entries from the landing page;
- replaced promotional capability wording with explicit implementation and
  architecture descriptions;
- retained Quantas Dark as the default theme;
- kept the Scientific UI Kit accessible from both navigation and Settings.

### Fixed

- replaced the incomplete component-probe exception list with a reusable Dash
  generated-component probe that discovers required explicit properties at
  runtime;
- added the required probe identifier for `dcc.Store`;
- applied the same probe implementation to pytest and the standalone Dash
  component audit, preventing the two checks from diverging.

### Existing foundation included in this alpha

- responsive Dash application shell;
- Scientific UI Kit and declarative form system;
- controlled native-HDF5 Result Explorer;
- module-aware adapters for Elasticity, SEISMIC, HA, QHA,
  Thermoelasticity, and the structurally separate EOS archive;
- lazy server-side report and plot construction with bounded artifact caching;
- Plotly renderers for Cartesian, polar, contour, surface, spherical, and panel
  specifications;
- replaceable workspace, result-store, and execution-backend seams for future
  server deployment.

## Unreleased

### Planned

- systematic scientific review of every module-specific Plotly view;
- improved Plotly export, camera, annotation, comparison, and unit controls;
- first complete executable workflow, beginning with Elasticity;
- local background-job execution with Quantas progress events;
- server-side worker and shared-cache implementations without changing page
  contracts.
