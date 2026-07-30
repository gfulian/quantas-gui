# Changelog

All notable changes to Quantas GUI will be documented in this file.

The project follows Semantic Versioning while the public interface remains under
active alpha development.

## 0.2.9a4 — 2026-07-30

This patch addresses the last failures reported by the complete Windows gate for
`0.2.9a3`. It does not change the Result Explorer interface or scientific
behaviour.

### Fixed

- apply the three remaining line-wrap changes required by Ruff `0.16.0`;
- publish derived exports through a writable file descriptor before calling
  `os.fsync`, avoiding `OSError: [Errno 9] Bad file descriptor` on Windows;
- add a regression test that verifies the descriptor supplied to the sync step
  is writable.

### Continuous integration

- clarify that the repository uses GitHub Actions rather than Travis CI;
- document that the test matrix checks out `gfulian/quantas` separately and
  installs the `dev/refactor` branch before installing Quantas GUI;
- keep the package-build job independent of a preinstalled backend because
  wheel and source-distribution creation only records runtime metadata.

### Validation

- the complete Windows validator passes in the maintainer environment,
  including Ruff lint and formatting, mypy, pytest, the Dash component audit,
  package builds and `twine check`;
- `173` tests pass against the supplied Quantas `2.0.0b7` source and `3`
  Dash-dependent tests are skipped only in the reduced review environment,
  where Dash is unavailable;
- GitHub Actions is the remaining independent gate before this snapshot is
  merged and tagged.

## 0.2.9a3 — 2026-07-30

This maintenance snapshot follows the first full Windows validation of
`0.2.9a2`. It does not change the scientific scope of the Result Explorer; it
corrects the quality gate, makes Windows setup more reliable and gives the
project documentation a clearer, more natural voice.

### Fixed

- apply the import ordering and formatting required by the pinned Ruff baseline;
- remove the unused plot-callback import and replace the deprecated
  `typing.ContextManager` alias;
- resolve the three reported mypy errors by renaming the application-profile
  title property, validating persisted numeric timestamps before conversion and
  supplying the required marker argument to Cartesian overlays;
- include `filelock` through the normal project installation path and add a
  regression check that keeps it a required runtime dependency;
- add `scripts\validate_windows.cmd`, allowing the complete Windows gate to run
  even when the machine blocks unsigned PowerShell scripts;
- propagate setup and check failures correctly from both Windows validators.

### Documentation

- rewrite the README, project state, roadmap, architectural decisions and
  development guides in more direct, human-readable English;
- explain why each architectural rule exists before listing its technical
  consequences;
- update Windows instructions to recommend the policy-independent batch
  validator while retaining a process-local PowerShell alternative;
- keep legal text, citation metadata and historical changelog entries factual
  rather than rewriting them for style alone.

### Validation

- source compilation passes for `src`, `tests` and `tools`;
- `171` tests pass against the supplied Quantas `2.0.0b7` source and `3`
  Dash-dependent tests are skipped because Dash is unavailable in the review
  environment;
- the exact Windows gate with Ruff `0.16.0`, mypy `2.3.0`, Dash `4.4.1`, package
  builds and `twine check` remains the final confirmation before this snapshot
  is pushed or tagged.

## 0.2.9a2 — 2026-07-30

### Changed

- remove the Scientific UI Kit from the standard page registry, desktop sidebar,
  mobile navigation, and ordinary Settings page; expose the isolated gallery,
  Settings, and About through `quantas-gui --ui-kit`;
- introduce explicit standard and UI Kit application profiles while preserving
  the same packaged assets, theme system, component callbacks, and Dash audit;
- make the WSGI entry point use conservative server defaults, including disabled
  debug/browser launch, secure-cookie policy, optional trusted hosts, and
  explicitly configured proxy-header trust;
- expose workspace, cache, execution, profile, and per-workflow lifecycle status
  through the health endpoint without exposing the workspace path;
- distinguish Result Explorer readiness from the complete public lifecycle
  required to execute each future workflow;
- remove unused Diskcache, Celery, and Redis extras so packaging does not imply a
  job backend that has not been selected or implemented; retain only the WSGI
  servers actually supported by the deployment guide.

### Added

- add portable cross-process workspace locks for native-result reads, writes,
  exports, and deletion on shared filesystems;
- add atomic publication for uploaded HDF5 files and scientific exports;
- add single-flight cache construction, shared factory errors, stale-flight-safe
  invalidation, and diagnostic counters for concurrent requests;
- add bounded browser serialization and callback error presentation that redact
  server paths and summarize large strings, mappings, sequences, arrays, and byte buffers;
- add validated, JSON-compatible job handles, event cursors, progress,
  cancellation, error, and result-ID contracts together with an explicit
  disabled execution backend before `0.3`;
- add security response headers, separate `/healthz` liveness from `/readyz`
  backend readiness, and expose process/cache/workspace diagnostics;
- add regression tests for cache concurrency, invalidation during construction,
  cross-process workspace deletion, closing-workspace rejection, atomic-output
  cleanup, path redaction, strict server settings, job serialization, readiness,
  and isolated application profiles.

### Validation

- `165` tests pass and `3` Dash-dependent tests are skipped in the reduced
  environment; source compilation passes for `src`, `tests`, and `tools`;
- wheel and source distributions build successfully through the declared
  setuptools backend, and their contents and core metadata have been inspected;
- the exact Windows Ruff, mypy, Dash `4.4.1` runtime, `twine check`,
  standard-profile, and `--ui-kit` gate remains required before closing `0.2`.

## 0.2.9a1 — 2026-07-30

### Changed

- decompose the Result Explorer callback surface into focused modules for active
  result lifecycle, tabs, tables, plots, messages, and downloads, retaining one
  small registration facade;
- move read-only EOS archive family and fit-table construction out of the generic
  Quantas result gateway;
- move scientific label normalization to a renderer-neutral presentation package
  while retaining a compatibility facade for existing imports;
- move the active-result store into the application shell so completed workflows
  can hand an opaque result reference to the Result Explorer across page navigation;
- add a controlled `register_result()` service operation for HDF5 results already
  produced in a workspace, without browser upload or arbitrary filesystem paths;
- distinguish disposable upload workspaces from workflow-owned workspaces when a
  result is closed;
- delegate table and plot grouping through the configured result backend instead
  of resolving module adapters a second time in the orchestration service.

### Added

- show whether a scientific plot selection is current, not yet built, or changed
  and awaiting rebuild;
- display a compact summary of the scientific selection that produced the cached
  PlotCollection;
- add separate reset actions for scientific selectors and Plotly appearance;
- add an immutable `ActiveResultState` handoff contract for workflow pages and
  the application-scoped Result Explorer store;
- add a reusable `tools/audit_result_explorer.py` command for report, PlotSpec,
  Plotly, and read-only checksum validation against native HDF5 files;
- add regression coverage for callback decomposition, application-scoped active
  results, workflow result registration, workspace ownership, backend grouping,
  and contour overlays with backend-default markers.

### Fixed

- supply the default translated marker when a scalar-coloured path is overlaid on
  a contour figure, preventing archived Thermoelasticity profile paths from
  failing after marker differentiation became explicit.

### Validation

- `135` tests pass and `3` Dash-dependent tests are skipped in the reduced
  environment; all supplied result families pass the reusable HDF5 audit, with
  large QHA tables and plots audited in separate lazy passes;
- the exact Windows Ruff, mypy, Dash runtime, build, and distribution gate remains
  the release criterion for this increment.

## 0.2.8a3 — 2026-07-29

### Fixed

- apply the exact Ruff `0.16.0` formatting requested by the Windows quality gate
  in scientific labels, selection adapters, the Thermoelasticity adapter, Plotly
  rendering, EOS table construction, and their regression tests;
- annotate compact informative-context values as `tuple[str, ...]`, resolving the
  final mypy inference conflict without casts or weakened checking;
- preserve the distinct Matplotlib marker variants used by Quantas, including
  uppercase and lowercase diamond markers, when translating to Plotly;
- assign a deterministic unused marker whenever a multi-series overlay contains
  a missing or duplicated source marker, so every visible Thermoelasticity
  component remains identifiable independently of colour and line style;
- apply the same marker differentiation to scalar-coloured profile overlays.

### Validation

- the project maintainer reported `134` pytest tests passing before this
  maintenance increment, with Ruff lint already green;
- `127` tests pass and `3` Dash-dependent tests are skipped in the reduced
  environment; regression coverage verifies seven distinct symbols for both
  ordinary and temperature-coloured Thermoelasticity overlays;
- the exact Windows Ruff format, mypy, pytest, Dash runtime, build, and
  distribution gate must be rerun for `0.2.8a3`.

## 0.2.8a2 — 2026-07-29

### Fixed

- normalize generic stiffness labels emitted as `C_IJ`, `C_{IJ}`, `C^T_{IJ}`,
  or `C^S_{IJ}` to the conventional presentation forms `C_{ij}`,
  `C^{T}_{ij}`, and `C^{S}_{ij}` without changing specific Voigt components;
- compact equivalent angstrom-volume units to `Å³` and prevent duplicate
  quantity/unit suffixes in axes, colorbars, table headers, and CSV headers;
- identify the Thermoelasticity domain figure explicitly as the QHA equilibrium
  volume field used to evaluate the calibrated elastic model over the stored
  pressure-temperature domain;
- keep the domain colorbar title visible as `Equilibrium volume (Å³)` by moving
  it closer to the plot and reserving sufficient right margin;
- deduplicate genuinely shared scalar colorbars in faceted panel figures while
  retaining separate bars when their scales or limits differ.

### Added

- expose public Thermoelasticity profile layout choices for overlay, faceted, or
  separate figures;
- expose public profile colour encoding by stiffness component, archived
  temperature, or neutral lines;
- preserve absolute/relative profile selection while allowing any advertised
  set of `C_{ij}` components to be drawn together in one overlay;
- summarize long stored pressure, temperature, and volume grids in read-only
  context badges while retaining exact values in the server-side inventory;
- add regression coverage for generic tensor notation, equivalent volume units,
  Thermoelasticity profile option forwarding, shared-versus-distinct panel
  colorbars, and the clarified domain family.

### Validation

- `125` tests pass in the available reduced environment and `3` Dash-dependent
  tests are skipped because the pinned Dash stack is unavailable there;
- representative Elasticity, SEISMIC, HA, QHA, Thermoelasticity, and EOS results
  were reopened through the public lifecycle API and all advertised default plot
  families rendered without unresolved generic tensor labels, duplicate units,
  or missing colorbar titles;
- the exact Windows Ruff, mypy, Dash runtime, package-build, and `twine check`
  gate must be rerun for `0.2.8a2`.

## 0.2.8a1 — 2026-07-29

### Fixed

- translate frontend-neutral Matplotlib grayscale strings such as `"0.35"` and
  `"0.65"` to CSS colours before constructing Plotly traces, restoring
  Thermoelasticity fit, profile, uncertainty-band, and domain figures;
- centralize portable colour handling for line, marker-edge, band, span, contour,
  surface, and polarization styles, also preventing the same incompatibility for
  EOS excluded-point and diagnostic styles;
- preserve all scientific arrays, units, labels, and PlotSpec semantics while
  applying the colour translation only in the Plotly presentation layer.

### Added

- expose one read-only EOS report family for every immutable archive fit record;
- show the selected EOS model, domain, fitted target or structural axis, result
  slot, relationship, acceptance state, solver, fitted parameters, uncertainties,
  parameter states, units, bounds, fit-quality metrics, covariance, correlation,
  derived quantities, warnings, and available diagnostics through public
  `quantas.api.eos` archive operations;
- add regression coverage for Matplotlib grayscale styles inside line and panel
  PlotSpecs and for public EOS fit-record tables with byte-for-byte archive
  immutability;
- validate the Result Explorer against representative native HDF5 results for
  Elasticity, SEISMIC, HA, QHA, three Thermoelasticity result forms, and EOS.

### Validation

- the complete `0.2.7a3` Windows quality gate is reported green by the project
  maintainer before this increment;
- `119` tests pass in the available reduced environment and `3` Dash-dependent
  tests are skipped because the pinned Dash stack is unavailable there;
- all supplied native result files open read-only, all report families build, and
  every advertised plot family renders through the public Quantas API after the
  portable-colour correction;
- the supplied EOS archive remains byte-for-byte unchanged after inventory, table,
  and plot inspection;
- the exact Windows Ruff, mypy, Dash runtime, package-build, and `twine check` gate
  must be rerun for `0.2.8a1`.

## 0.2.7a3 — 2026-07-29

### Fixed

- use separately named `selected_table_family` and `selected_plot_family`
  variables in the tab callback, eliminating the remaining mypy union between
  table and plot descriptors;
- apply the exact Ruff `0.16.0` formatter layout to the two residual source
  files reported by the Windows gate;
- retain the `0.2.7a2` scientific-label import and `Quantity (unit)`
  normalization fixes without changing Result Explorer behaviour.

### Validation

- the preceding Windows run reports Ruff lint passing and `125` pytest tests
  passing;
- the remaining formatter and mypy diagnostics are addressed in this
  maintenance increment;
- the exact Windows gate must be rerun to record the final Ruff format and mypy
  result for `0.2.7a3`.

## 0.2.7a2 — 2026-07-29

### Fixed

- import the native scientific-label formatter in the Result Explorer plot
  panel, restoring every inventory-driven plot view after the `0.2.7a1`
  scientific-selection regression;
- keep table-family and plot-family descriptors in separately typed callback
  variables, removing the mypy assignment conflict introduced by the shared
  local name;
- normalize table headers, Plotly axes, hover labels, and colorbars to the
  presentation form `Quantity (unit)`, including legacy labels such as
  `E / GPa`, without rewriting scientific ratios such as `C_P / C_V`;
- normalize unbraced numeric exponents in native labels, so plain units such as
  `km s^-1` and MathText units such as `km s$^{-1}$` compare and render
  consistently;
- apply the Ruff `0.16.0` lint simplifications, import ordering, and formatter
  layout reported by the exact Windows quality gate;
- remove the unused `dash_ag_grid.*` mypy override while retaining the required
  top-level third-party import boundary.

### Validation

- `116` tests pass in the available Linux environment and `3` Dash-dependent
  tests are skipped because the pinned Dash stack is unavailable there;
- source compilation and public Plotly rendering regression tests pass;
- the exact Windows Ruff, mypy, Dash runtime, build, and `twine check` gate must
  be rerun before this correction is considered closed.

## 0.2.7a1 — 2026-07-29

### Fixed

- load the Dash AG Grid legacy base and Quartz stylesheets from the application
  factory, completing the `theme="legacy"` contract used by report grids and
  restoring actual cells, headers, pagination, filtering, and sorting in the
  browser;
- build the default report family when the Tables tab is entered, so initial
  table creation no longer depends on a secondary dynamically inserted callback;
- include the repository workflow and issue-template files required by the
  packaged quality tests, making the source distribution self-consistent;
- preserve the dedicated report-grid CSS and raw numeric payload introduced in
  `0.2.6a1` while keeping dark/light custom properties on top of the official
  Quartz legacy theme.

### Added

- add immutable, browser-light `PlotSelectionSchema`,
  `ScientificSelectionField`, and `PlotBuildSelection` contracts;
- derive scientific property and context controls from public
  `describe_plots()` inventories, including exact stored coordinates and
  read-only contextual metadata;
- add an explicit **Build selected view** action, separate from the collapsed
  Plotly presentation toolbar;
- map selections through public module adapters for Elasticity, SEISMIC, HA,
  QHA, and Thermoelasticity; EOS continues to use explicit record-specific
  family keys in the generic read-only explorer;
- include the canonical scientific selection in the server-side plot-cache key,
  so equal selections reuse one collection and distinct selections remain
  isolated;
- add regression coverage for selection serialization, exact inventory values,
  cache separation, public HA selected-coordinate plotting, and the AG Grid
  legacy-theme asset contract;
- record ADR-027 for explicit, inventory-driven scientific selections.

### Validation

- `114` tests pass from both the clean source tree and the extracted source
  distribution in the available Linux environment; `3` Dash-dependent tests are
  skipped because the pinned Dash stack is unavailable there;
- source compilation, public Quantas HA integration, wheel construction, source
  distribution construction, archive hygiene, and isolated wheel import pass;
- the exact Windows Ruff, format, mypy, Dash runtime, visible AG Grid rendering,
  Windows build, and `twine check` gate remains required before this alpha
  increment is considered closed.

## 0.2.6a1 — 2026-07-29

Result Explorer runtime rendering correction for tables, Dash 4 themes, exact
contours, and public SEISMIC polarization overlays.

### Fixed

- removed a CSS-class collision between the Results landing layout and Dash AG
  Grid that left report tables present but visually unrendered;
- report grids now use a dedicated class and compact bounded height derived from
  the number of visible rows;
- requested isoline counts now use explicit start, end, and spacing values so a
  new request replaces the source contour set instead of relying on Plotly's
  automatic level selection;
- native plot descriptions apply the same bounded LaTeX-to-Unicode conversion
  as dropdown labels, eliminating literal strings such as ``$V_P$`` outside
  MathJax-enabled figures;
- light-theme event and JSON payload blocks now use light surfaces and readable
  foreground tokens;
- the light muted-text token now meets normal-text contrast against the primary
  page background.

### Added

- a Dash 4 design-token bridge for dropdowns, checklists, sliders, disabled
  states, and interactive fills in both Quantas themes;
- public SEISMIC plot construction with polarization layers when
  ``describe_plots()`` advertises tracked axes; no overlay is invented when the
  public context is restricted to ``False``;
- display-only polarization length in addition to visibility, stride, line
  width, and colour;
- 3D polarization normalization and relative scaling aligned with the current
  Quantas Matplotlib renderer;
- regression coverage using a real public SEISMIC calculation to prove that
  tracked axes reach both 2D ``AxisFieldLayer`` and 3D ``VectorFieldLayer``
  PlotSpecs;
- static and numerical theme, table-class, scientific-label, and exact-contour
  regression checks.

### Changed

- the collapsed figure-control drawer uses adaptive cards, bounded scrolling,
  and denser responsive polarization controls; when opened on wide screens it
  becomes a side workbench so the figure remains visible beside the controls;
- SEISMIC PlotSpecs retain full public polarization layers server-side while the
  GUI applies visual decimation without reopening the result or recomputing the
  scientific field.

### Validation status

- ``107`` tests pass in the reduced Linux environment and ``3`` Dash-dependent
  tests are skipped because Dash is unavailable there;
- public SEISMIC tracking was exercised through ``quantas.api`` for spherical
  and three-dimensional plots;
- source compilation, wheel construction, source-distribution construction,
  archive-content checks, and an isolated wheel import pass;
- the exact Windows gate remains required for Ruff ``0.16.0``, mypy ``2.3.0``,
  Dash ``4.4.1``, Dash AG Grid ``35.2.0``, Plotly ``6.9.0``, Windows build, and
  ``twine check``.

## 0.2.5a1 — 2026-07-29

Result Explorer scientific-figure presentation controls and Plotly fidelity
corrections.

### Added

- renderer-only line-width and line-colour controls for Cartesian, polar, and
  contour overlays;
- selectable isoline count for Cartesian and spherical contour plots;
- Cartesian and crystallographic directional labels for principal-plane polar
  plots, spherical maps, and 3D directional surfaces;
- SEISMIC polarization controls for visibility, visual stride, line width, and
  colour, applied to public `AxisFieldLayer` and `VectorFieldLayer` overlays;
- explicit origin-centred 3D axes modelled on the current Quantas Matplotlib
  surface renderer;
- Unicode formatting of the bounded Quantas mathematical-label subset in native
  Dash selectors, while Plotly continues to use the source MathJax labels;
- regression tests for presentation-only line overrides, contour levels,
  colorbar placement, polar/spherical/3D directional labels, 3D axes, and
  polarization controls.

### Changed

- spherical-map colorbars are horizontal, compact, and placed immediately below
  the projection, matching the Matplotlib visual convention more closely;
- Cartesian and 3D colorbars are positioned close to the plotting domain with
  complete quantity-and-unit titles;
- the collapsed figure-control drawer now exposes sections according to the
  selected public PlotSpec and the actual presence of polarization layers;
- figure axis and colorbar labels consistently use the public
  `Quantity (unit)` contract without duplicating units.

### Deferred

- Thermoelasticity geological-layer backgrounds remain deferred until Quantas
  exposes layer boundaries and presentation-neutral metadata through the public
  PlotSpec. Quantas GUI does not infer them from private result payloads.

### Validation status

- `95` tests pass in the reduced Linux environment and `3` Dash-dependent tests
  are skipped because Dash is unavailable there;
- source compilation passes for `src`, `tests`, and `tools`;
- the exact Windows gate remains required for Ruff `0.16.0`, mypy `2.3.0`, Dash
  `4.4.1`, Dash AG Grid `35.2.0`, Plotly `6.9.0`, build, and `twine check`.

## 0.2.4a1 — 2026-07-28

Result Explorer table-export correction and first plot-kind-specific presentation
controls.

### Added

- a separate collapsible Scientific exports area driven by public
  `quantas.api.registry` export operations;
- immediately executable public exports for Elasticity, SEISMIC, and the complete
  QHA pressure-temperature table;
- explicit disabled descriptions for HA, Thermoelasticity, and EOS exports that
  still require scientific selections;
- a collapsed Figure controls drawer grouped into interaction, visibility, colour
  and scale, contours, spherical projection, and three-dimensional view sections;
- PlotSpec-specific control profiles so irrelevant controls remain hidden;
- server-side export paths and cache entries scoped by workspace, result, and
  operation.

### Changed

- Dash AG Grid now receives raw numeric and boolean cells for correct sorting and
  filtering while Quantas formatting metadata remains the displayed value;
- the generic table CSV is labelled as a complete ReportTable view export and is
  kept separate from official scientific exports;
- derived download names are sanitized and remain contained in the controlled
  workspace;
- completed the two residual Ruff corrections reported after `0.2.3a2`.

### Validation status

- `87` tests pass in the reduced Linux environment and `3` Dash-dependent tests
  are skipped because Dash is unavailable there;
- source compilation passes for `src`, `tests`, and `tools`;
- the exact Windows gate remains required for Ruff `0.16.0`, mypy `2.3.0`, Dash
  `4.4.1`, Dash AG Grid `35.2.0`, Plotly `6.9.0`, build, and `twine check`.

## 0.2.3a2 — 2026-07-28

Maintenance-only cleanup after the first complete Windows validation of the
Quantas `2.0.0b7` lifecycle integration.

### Fixed

- typed plot-family construction costs with the shared `ArtifactCost` literal;
- widened the EOS compact-inventory annotation to support optional selected-plot
  entries;
- removed an unused renderer palette lookup and simplified hemisphere flipping
  without changing projected scientific data;
- corrected import ordering and constant-attribute assignments reported by Ruff;
- applied the repository Ruff formatter to the source, tests, and tools touched by
  the lifecycle increment.

### Validation status

- all Ruff and mypy defects reported by the `0.2.3a1` Windows quality gate have
  been addressed in source;
- `79` non-Dash tests pass in the reduced Linux build environment, with `3`
  Dash-dependent tests skipped because Dash is unavailable there;
- source compilation passes for `src`, `tests`, and `tools`;
- the exact pinned Windows quality gate remains the release acceptance check for
  Ruff `0.16.0`, mypy `2.3.0`, Dash `4.4.1`, Dash AG Grid `35.2.0`, Plotly `6.9.0`,
  package build, and `twine check`.

## 0.2.3a1 — 2026-07-28

Public lifecycle integration with Quantas `2.0.0b7` while remaining inside the
Result Explorer milestone.

### Added

- immutable backend compatibility diagnostics covering version, registry, module
  operations, plot inventories, public PlotSpec classes, input generation, exports,
  and EOS persistence;
- shell-only degraded mode for absent, incompatible, or incomplete Quantas backends;
- accessible disabled scientific navigation and recovery diagnostics;
- public-lifecycle integration documentation and architecture regression tests;
- read-only EOS dataset, slot, record, state, and record-specific plot inventory.

### Changed

- made `quantas>=2.0.0b7,<2.1` a required runtime dependency;
- migrated result identification and reopening to `quantas.api.registry`;
- migrated report construction to public `build_report()` operations;
- migrated plot-family discovery to public `describe_plots()` inventories;
- migrated the Plotly renderer from class-name matching to typed dispatch using
  `quantas.api.plotting`;
- retained lazy server-side report and plot construction and lightweight browser state;
- updated CI and Windows validation to install the constrained companion backend.

### Security and architecture

- block scientific uploads before decoding or workspace writes when the backend gate
  is not ready;
- reject private Quantas namespace and direct `h5py` imports from GUI runtime source;
- preserve EOS archive immutability during generic inspection.

### Validation status

- `79` tests pass against the actual Quantas `2.0.0b7` source tree;
- `3` Dash-dependent tests are skipped in the build container because Dash is absent;
- wheel and source distributions build successfully, and an isolated wheel smoke test
  confirms version, required backend metadata, packaged assets, and lifecycle files;
- the exact Ruff, mypy, Dash runtime, `twine check`, and cross-platform CI gate remain
  to be executed for this snapshot.

## 0.2.2a1 — 2026-07-27

First scientific-visual convergence pass for the Result Explorer.

### Changed

- made the operating-system colour preference the default for new browser profiles
  and followed later system light/dark changes while that mode remains selected;
- increased Plotly figure space and made scientific figure backgrounds transparent so
  the application theme controls on-screen presentation and exported images retain a
  neutral background;
- enabled MathJax in the shared Plotly graph and preserved complete Quantas axis labels
  without appending duplicate units;
- standardized stronger theme-aware axes, ticks, grids, hover labels, legends, and
  vertical colorbar titles;
- rendered polar specifications as larger line-based scientific panels, preserving
  source colors, line styles, optional markers, radial limits, and panel identity;
- replaced marker-cloud spherical maps with continuous projected contour fields,
  hemisphere boundaries, Cartesian direction labels, extrema markers, and projected
  axial-vector overlays aligned with the current Quantas Matplotlib renderer;
- improved dark-theme slider marks and tooltips, including the shared surface-opacity
  control.

### Added

- early browser theme bootstrap for first-paint system-theme selection;
- regression tests for MathJax activation, slider visibility, system-theme following,
  line-based polar plots, continuous spherical contours, transparent backgrounds, and
  vertical colorbar labels;
- a documented renderer-fidelity policy for comparing Plotly output with the public
  Quantas plot specification and its Matplotlib reference rendering.

### Validation status

- source compilation and the available local test suite pass;
- synthetic public Quantas polar and spherical specifications have been rendered through
  the Plotly dispatcher;
- final Dash 4.4.1, Ruff, mypy, cross-platform CI, and representative native-HDF5 visual
  review remain required before closing milestone `0.2`.

## 0.2.1a6 — 2026-07-27

Repository-governance and CI supply-chain hardening after completion of the
application foundation.

### Security

- pinned all GitHub Actions to immutable full commit SHAs;
- updated GitHub-owned actions to their current Node.js 24 release lines;
- disabled persisted checkout credentials and retained read-only workflow token
  permissions;
- added pull-request dependency review with a moderate-severity failure policy;
- added concurrency cancellation, job timeouts, strict artifact handling, and
  short artifact retention;
- added an aggregate `CI gate` suitable for a single required ruleset check;
- expanded private vulnerability reporting guidance and issue routing.

### Documentation

- documented the exact `main` ruleset, merge policy, Actions restrictions,
  Advanced Security settings, and maintainer-account protections;
- recorded protected-branch and immutable-CI decisions in the architectural
  decision log;
- documented the branch-and-pull-request workflow for future development.

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
