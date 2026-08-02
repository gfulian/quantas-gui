# Changelog

All notable changes to Quantas GUI will be documented in this file.

The project follows Semantic Versioning while the public interface remains under
active alpha development.

## 0.4.0a4 — 2026-08-02

This closing alpha completes the SEISMIC milestone. It does not change the
scientific calculation or native result format; it records the validated state,
updates the workflow catalogue and makes the operational documentation easier
to follow.

### Changed

- mark milestone `0.4` complete and identify `0.5` — HA/QHA as the next active
  milestone;
- mark both HA and QHA as the next workflow family in the catalogue while
  keeping their actions disabled until the GUI implementations exist;
- make the catalogue's **Next** label derive from each workflow milestone rather
  than from a hard-coded version;
- add a user-oriented SEISMIC workflow guide covering input, sampling levels,
  progress, failure states, downloads and the two three-dimensional surface
  families;
- update the README, roadmap, project state, documentation index and citation
  metadata for the closing baseline.
- align the required and CI-constrained Quantas backend with the corrected
  `2.0.0b8` release label used by the local CI checkout.

### Validation

- record the complete pinned Windows gate as green for the preceding executable
  and Result Explorer implementation;
- record successful real-data runs from a VASP OHAp output and a CRYSTAL calcite
  output;
- retain numerical agreement with the public API within `rtol=1e-14`,
  `atol=1e-14` for averages and isotropic velocities and `rtol=1e-12`,
  `atol=1e-12` for sampled phase, group and enhancement fields;
- add catalogue regressions for the completed SEISMIC state and the next HA/QHA
  milestone.

## 0.4.0a3 — 2026-08-02

### Changed

- rename the SEISMIC 3D plot families in the Result Explorer to **General
  scalar-field surface** and **Acoustic wave surface**;
- allow several scalar properties to be selected and built in one operation,
  after which the generated figures can be switched without rebuilding the
  scientific collection;
- explain that the general scalar family is intended primarily for anisotropy,
  shear splitting, velocity ratios, power-flow angle and enhancement, while the
  acoustic family is the clearer route to phase, slowness and group surfaces;
- keep all scientific availability, geometry and values sourced from the public
  Quantas plot inventory.

### Validation

- add adapter regressions for the revised family labels and descriptions;
- verify that the scalar-property selector is multi-valued with a bounded
  one-property default;
- verify that every selected scalar property reaches the public
  `SurfaceOptions` in one build request.

## 0.4.0a2 — 2026-08-01

### Added

- add the executable Dash SEISMIC page with manual, Quantas, CRYSTAL and VASP
  input paths;
- add reusable complete and triangular stiffness parsing shared with Elasticity;
- expose density, angular sampling, hemisphere, phase/group/enhancement level,
  polarization continuity, numerical tolerances and physical tensor rotation;
- add non-blocking submit, persistent polling, monotonic progress, ordered activity,
  cooperative cancellation and distinct failed/cancelled presentations;
- add the compact public-report summary, native HDF5 and report downloads, sampled
  CSV export and automatic Result Explorer handoff;
- mark SEISMIC available in the Workflows catalogue while keeping backend and GUI
  readiness distinct.

### Changed

- retain the exact `quantas==2.0.0b7` CI constraint for the current capability
  snapshot; the backend version-label correction to `2.0.0b8` remains a separate
  backend change;
- move stiffness text parsing and formatting into `workflows.common` so
  Elasticity and SEISMIC share one structural input convention.

### Validation

- compare process-backed phase, group and enhancement fields with the direct
  public API within `rtol=1e-12`, `atol=1e-12`;
- preserve stiffness exactly and elastic averages and isotropic velocities within
  `rtol=1e-14`, `atol=1e-14`;
- verify native HDF5 reopening, sampled CSV export, input import, lightweight
  events, monotonic progress, unstable-medium failure and opaque result handoff;
- add form, page, callback-registration and prefix-aware catalogue regressions.

## 0.4.0a1 — 2026-08-01

### Added

- add the server-side SEISMIC request contract with density, spherical sampling,
  calculation level, polarization tracking, numerical tolerances and physical
  tensor rotation;
- add a public-API-only SEISMIC adapter, process worker, controlled
  CRYSTAL/VASP/Quantas input import, native HDF5 publication and Result Explorer
  handoff;
- register the SEISMIC process handler and make workflow readiness require the
  new public `seismic.create_input()` capability without disabling Result
  Explorer support for older result-only backends;
- enable the local execution service when either Elasticity or SEISMIC exposes a
  complete executable public lifecycle.

### Validation

- compare the process result with a direct public API run, preserving density and
  stiffness and matching elastic averages and isotropic velocities within
  `rtol=1e-14`, `atol=1e-14`;
- compare sampled phase, group and enhancement fields within `rtol=1e-12`,
  `atol=1e-12`, including one non-trivial physical tensor rotation;
- verify monotonic progress, lightweight events, unstable-tensor failure, atomic
  HDF5 publication, reopening and opaque Result Explorer handoff;
- verify shared Quantas input, VASP density extraction and explicit rejection of
  missing density.

### Notes

- this tranche intentionally does not expose the Dash SEISMIC form yet;
- the backend capability snapshot is still labelled `2.0.0b7`; the planned
  backend correction is `2.0.0b8`.


## 0.3.0a7 — 2026-07-31

This closing alpha completes the Elasticity milestone and turns the previously
empty Workflows page into an operational catalogue. It does not change
Elasticity calculations, numerical options or persisted HDF5 content.

### Added

- populate `/workflows` with accessible cards for Elasticity, SEISMIC, HA, QHA,
  Thermoelasticity and EOS;
- distinguish public Quantas API readiness from GUI workflow availability;
- expose **Start workflow** only for the completed Elasticity calculator;
- show each workflow's principal input, canonical persisted result and roadmap
  milestone without generating scientific forms mechanically from the registry;
- add responsive catalogue styling and regression tests for available, planned
  and incomplete-backend states.

### Project state

- close milestone `0.3` with `0.3.0a7` as the approved Elasticity baseline;
- identify `0.4` — SEISMIC as the next GUI milestone;
- retain the shared process-backed execution, feedback, download and Result
  Explorer handoff architecture as the reference implementation for later
  calculators.

### Validation

- the complete Windows gate is reported green for Ruff lint, Ruff format, mypy,
  pytest, Dash component audit, build and distribution checks;
- the final Windows pytest run reports `218 passed`;
- the executable workflow and Result Explorer handoff are validated on desktop
  and from an Android browser over a private local network;
- the 3D figure's reduced portrait height remains a documented non-blocking
  limitation because the figure is usable in portrait and displays correctly in
  landscape.

## 0.3.0a6 — 2026-07-31

This gate-cleanup alpha applies the final Ruff formatting baseline after the
triangular Elasticity input change. It does not change scientific behaviour,
workflow state, persisted HDF5 content or the public Quantas contract.

### Fixed

- format the zero-padded triangular-matrix predicates exactly as required by
  Ruff `0.16.0`.

### Validation

- the Windows gate reports Ruff lint and mypy green and `218` pytest tests
  passing; the only reported failure before this correction was the formatter
  difference fixed above;
- the executable Elasticity workflow and Result Explorer handoff were exercised
  successfully from an Android phone over the local network;
- the 3D view remains usable in portrait and displays correctly in landscape;
  its reduced portrait height is recorded as a minor, non-blocking responsive
  limitation rather than changed late in this tranche.

## 0.3.0a5 — 2026-07-31

This corrective alpha broadens direct Elasticity matrix paste without changing
the public Quantas scientific contract or persisted result format.

### Added

- accept compact upper-triangular Voigt matrices with row lengths
  `6, 5, 4, 3, 2, 1`;
- accept compact lower-triangular matrices with row lengths
  `1, 2, 3, 4, 5, 6`;
- accept full 6 × 6 upper- or lower-triangular matrices whose omitted strict
  triangle is explicitly padded with zeros;
- expand accepted triangular representations into one canonical symmetric
  6 × 6 matrix before constructing the public Elasticity request;
- document the accepted paste layouts directly beside the textarea.

### Safety and validation

- a full 6 × 6 matrix containing values in both triangles is preserved exactly
  and is not silently averaged or symmetrized; final scientific validation
  remains the responsibility of Quantas;
- mixed or ambiguous compact row-length patterns are rejected with a structural
  form error;
- regression tests cover compact upper and lower triangles, zero-padded forms,
  request construction, malformed layouts and preservation of genuinely
  asymmetric full matrices;
- the complete available suite passes against Quantas `2.0.0b7`: `202 passed`,
  with four UI-runtime tests skipped only because the pinned Dash stack is not
  installed in the review container.

## 0.3.0a4 — 2026-07-31

This corrective alpha closes the remaining Windows static-gate findings and
repairs the second stage of the Elasticity-to-Result-Explorer handoff. It does
not change scientific inputs, numerical results or persisted HDF5 content.

### Fixed

- apply the final Ruff formatting change in the Elasticity import service;
- remove a mypy name redefinition in the activity renderer and keep the viewer
  severity narrowed to the public `MessageLevel` literal contract;
- separate active-result session publication from Dash Pages navigation so the
  global `q-results-session` store is committed before `/results` is requested;
- navigate only after the stored active result matches the successful Elasticity
  workflow handoff, preventing unrelated session changes from redirecting the
  application;
- make the Result Explorer shell react explicitly to the current pathname as
  well as the active-result session;
- add a one-shot page hydration trigger so the shell, header and initial Overview
  tab consume the committed workflow result only after the dynamically mounted
  Result Explorer components exist;
- add regression coverage for handoff ordering, page hydration, callback inputs
  and mismatched or unrelated result sessions.

### Validation

- all orchestration return branches have been checked against the exact callback
  output arity after removing direct navigation from the submit/poll callback;
- the complete available source suite passes in the review environment; the
  pinned Windows Ruff, mypy, Dash audit and live browser gate remain the final
  acceptance evidence for this correction.

## 0.3.0a3 — 2026-07-31

This corrective alpha closes the first Windows gate findings from `0.3.0a2` and
repairs the workflow-to-Result-Explorer navigation path. It does not add new
scientific controls or change Elasticity results.

### Fixed

- remove the unused execution-service import and apply the Ruff `0.16.0`
  import-order and formatting baseline to the new Elasticity files and tests;
- narrow message levels, external-interface values, imported stiffness and
  progress metadata so the complete GUI source satisfies the declared mypy
  contract;
- replace the brittle assertion that rejected explanatory text about inferred
  crystal symmetry with a schema-level check proving that no manual symmetry
  field exists;
- configure the shell `dcc.Location` with `refresh="callback-nav"` and update
  its `href` from the Elasticity callback, allowing Dash Pages to render
  `/results` after the opaque active-result session is stored;
- add a regression assertion for callback-aware navigation and the Result
  Explorer handoff output;
- reject imported sources that contain no usable 6 × 6 stiffness matrix with a
  clear structural error.

### Validation

- the complete non-UI suite passes against Quantas `2.0.0b7`: `195 passed`,
  with four tests skipped only because the pinned Dash stack is unavailable in
  the review container;
- the original Windows report is fully accounted for in the patch; the pinned
  Ruff, mypy, Dash audit and live browser handoff must be rerun in the Windows
  worktree before this corrective alpha is accepted.

## 0.3.0a2 — 2026-07-31

This alpha connects the process-backed Elasticity service to the first complete
scientific workflow page. It adds source import, declarative inputs, persistent
job feedback, completion summary and Result Explorer handoff without moving
scientific responsibility into Dash callbacks.

### Added

- add the executable `/elasticity` page with a declarative job-name field and a
  monospaced multiline 6 × 6 stiffness matrix in GPa;
- import shared Quantas text input, CRYSTAL output and extensionless VASP
  `OUTCAR` files through public `quantas.api.elasticity` operations;
- retain the shared input convention while deliberately consuming no density
  or manually selected symmetry in the Elasticity workflow;
- expose public 2D/3D sampling choices, 3D property selection and optional
  physical XYZ or 3 × 3 tensor transformation;
- add non-blocking submit, polling, cooperative cancel and browser-refresh-safe
  state using only opaque handles, cursors and result references;
- add bounded Calculation activity tabs for All, Info, Warnings and Errors,
  including semantic icons and text labels;
- add explicit queued, running, cancelling, succeeded, succeeded-with-warning,
  failed and cancelled presentations;
- add a compact completion summary from public report tables, native HDF5 and
  report downloads, diagnostic-log download after failure, and direct handoff
  to the shared Result Explorer;
- embed a deterministic public-API report in the HDF5 before atomic
  publication;
- choose bounded internal 3D process batches to provide useful progress events
  for larger angular grids without exposing a technical batch-size control or
  changing scientific data;
- disable the executable page visibly when no execution backend is available,
  while retaining the replaceable server-ready execution contract.

### Validation

- add form tests for supported fields, paste parsing, source provenance,
  selected-source requirements, hidden defaults and progress batch policy;
- add public import tests for a Quantas input carrying shared density metadata,
  synthetic CRYSTAL output and extensionless VASP `OUTCAR`;
- verify that an unstable tensor completes with warnings, persists no fabricated
  directional fields and remains openable in the Result Explorer;
- verify ordered progress counters, monotonic progress and deterministic report
  text inside the native HDF5;
- add a real CLI equivalence test and compare stiffness exactly, compliance and
  Voigt–Reuss–Hill values at `rtol=1e-14`, `atol=1e-14`, and stored 3D data at
  `rtol=1e-12`, `atol=1e-12`;
- pass `195` tests, with four Dash-runtime tests skipped only because the pinned
  UI packages are unavailable in the review container.

### Remaining release gates

- run Ruff, mypy, the Dash 4.4.1 component audit, full wheel/source checks and
  browser interaction tests in the pinned Windows environment;
- validate dark/light/system themes, desktop/mobile layout, keyboard focus,
  disabled controls and live failure/cancellation behaviour.

## 0.3.0a1 — 2026-07-30

This is the first engineering alpha of the Elasticity milestone. It establishes
background execution and the public-API workflow service before the Dash form
and page callbacks are connected.

### Added

- add a replaceable local execution backend that starts scientific work in a
  separate `spawn` process and persists job status, ordered events and
  cancellation requests inside the controlled workspace;
- add process-crash reconciliation, bounded monotonic progress, sanitised
  serialisable failures and cleanup of partial outputs;
- publish successful native Quantas HDF5 results atomically and expose only
  opaque job, workspace and result identifiers to browser-facing layers;
- add a typed Elasticity request, a public `quantas.api.elasticity` adapter, a
  process-side worker and an application service for request persistence,
  polling, cancellation and Result Explorer handoff;
- enable local Elasticity execution only when the installed Quantas backend
  advertises the compatible public lifecycle; keep server-mode execution
  disabled until a shared queue-backed implementation is supplied;
- add an operational Elasticity audit documenting the current public contract,
  event inventory, density discrepancy, decomposition and remaining work.

### Validation

- add process tests for successful publication, ordered event cursors,
  polling through a recreated backend instance, cooperative cancellation, hard
  worker crashes, sanitised exceptions and two concurrent jobs with isolated
  workspaces and results;
- add workflow tests proving that density and manual symmetry are absent,
  physical rotation uses the public Quantas contract, and the process result
  matches a direct `quantas.api.elasticity` calculation;
- verify exact stiffness preservation, compare compliance and
  Voigt–Reuss–Hill averages with `rtol=1e-14` and `atol=1e-14`, and compare
  directional extrema plus stored 2D/3D arrays with `rtol=1e-12` and
  `atol=1e-12`;
- verify native HDF5 reopening and opaque handoff to the shared Result Explorer;
- pass `184` tests against Quantas `2.0.0b7`, with three Dash-dependent tests
  skipped because the pinned UI stack is absent from the review environment;
- build the `0.3.0a1` wheel successfully; Ruff, mypy, the pinned component
  audit, complete source/wheel checks and the end-to-end CLI comparison remain
  Windows release gates.

### Not yet included

- the declarative Elasticity form, Dash callbacks and final workflow page;
- server-side shared queue or persistent multi-worker process ownership;
- a stronger backend cancellation token than observer/checkpoint-based
  cooperative cancellation.

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

- the maintainer's Windows run reported Ruff lint and mypy green and reached
  `182` passing tests before the two atomic-output failures fixed here;
- `173` tests pass against the supplied Quantas `2.0.0b7` source and `3`
  Dash-dependent tests are skipped because Dash is unavailable in the review
  environment;
- the complete Windows gate remains the final confirmation for `0.2.9a4`.

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
