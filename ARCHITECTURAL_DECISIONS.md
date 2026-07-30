# Quantas GUI architectural decisions

This file records choices that should remain stable across more than one feature
or release. It is not a list of current bugs or unfinished tasks; those belong
in [PROJECT_STATE.md](PROJECT_STATE.md) or the issue tracker.

Each entry explains the reason for the choice, the decision itself and the
practical consequences. A decision marked **Accepted** guides new work. If a
later decision replaces it, the older entry remains here as **Superseded** so
that the history stays understandable.

## Decision index

| ID | Decision | Status |
|---|---|---|
| ADR-001 | Current and legacy source hierarchy | Accepted |
| ADR-002 | Quantas GUI is an independent package | Accepted |
| ADR-003 | The GUI depends only on the public Quantas API | Accepted |
| ADR-004 | Scientific and presentation responsibilities remain separate | Accepted |
| ADR-005 | Quantas emits frontend-neutral results, reports, plots and events | Accepted |
| ADR-006 | Shared UI infrastructure is generic; scientific selection is module-specific | Accepted |
| ADR-007 | The application is local-first and server-ready | Accepted |
| ADR-008 | Browser state remains lightweight and opaque | Accepted |
| ADR-009 | Workspaces and file access are controlled server-side | Accepted |
| ADR-010 | Execution, cache, result storage and workspace services are replaceable | Accepted |
| ADR-011 | Native Quantas HDF5 is the persistence boundary | Accepted |
| ADR-012 | Plotly and Dash AG Grid are GUI renderers, not scientific backends | Accepted |
| ADR-013 | Visual transforms are distinct from scientific transforms | Accepted |
| ADR-014 | Result construction is lazy and cacheable | Accepted |
| ADR-015 | EOS remains session-oriented and structurally separate | Accepted |
| ADR-016 | Scientific forms are declarative and validated in layers | Accepted |
| ADR-017 | The CLI is an audit reference, not a GUI runtime dependency | Accepted |
| ADR-018 | Appearance settings are presentation-only and browser-local | Accepted |
| ADR-019 | Dash component compatibility is versioned and tested explicitly | Accepted |
| ADR-020 | Responsive, accessible and cross-platform behaviour is part of completion | Accepted |
| ADR-021 | Public versions follow capability milestones | Accepted |
| ADR-022 | The default branch is protected and changes flow through pull requests | Accepted |
| ADR-023 | CI uses least privilege and immutable action references | Accepted |
| ADR-024 | Plotly preserves the scientific visual semantics of Quantas plots | Accepted |
| ADR-025 | Quantas is required and compatibility is capability-based | Accepted |
| ADR-026 | Public lifecycle inventories are the scientific discovery boundary | Accepted |
| ADR-027 | Scientific plot selections are explicit and inventory-driven | Accepted |
| ADR-028 | Completed workflows hand off opaque result references to the shared Explorer | Accepted |
| ADR-029 | Result access and artifact construction are concurrency-coordinated | Accepted |
| ADR-030 | Long workflows run outside HTTP callbacks with persistent job state | Accepted |
| ADR-031 | The Scientific UI Kit is an isolated application profile | Accepted |

---

## ADR-001 — Current and legacy source hierarchy

**Status:** Accepted  
**Date:** 2026-07-26

Quantas `dev-refactor` is the authority for current scientific behaviour,
architecture, public APIs, tests and native formats. Quantas `0.9.1` remains
useful for historical behaviour, legacy formats and explicit numerical
comparison, but it is not a design template for the refactored packages.

When sources disagree, current code and tests take precedence and the conflict
should be documented rather than guessed away.

## ADR-002 — Quantas GUI is an independent package

**Status:** Accepted  
**Date:** 2026-07-26

The graphical application is distributed separately:

```text
Distribution: quantas-gui
Python package: quantas_gui
Launcher: quantas-gui
```

Quantas remains usable as a library and command-line application without Dash,
Plotly or browser dependencies. The GUI can therefore follow its own release
schedule while both packages share one environment during development.

## ADR-003 — The GUI depends only on the public Quantas API

**Status:** Accepted  
**Date:** 2026-07-26

Scientific integration goes through `quantas.api`, including the registry,
module namespaces, plotting contracts, profiles, exports and interoperability
operations.

The GUI does not import `quantas.cli`, `quantas.modules`, private calculators,
internal HDF5 implementations, Rich renderers or Matplotlib renderers. When a
needed operation is missing, it should be added deliberately to the public API
instead of bypassed through a private import.

## ADR-004 — Scientific and presentation responsibilities remain separate

**Status:** Accepted  
**Date:** 2026-07-26

Quantas owns formulas, methods, tolerances, units, precision, typed scientific
objects, calculations and persistence. Quantas GUI owns forms, orchestration,
interaction, tables, figures, themes and supported view exports.

A visual convenience is never a valid reason to alter scientific behaviour in
the GUI.

## ADR-005 — Quantas emits frontend-neutral results, reports, plots and events

**Status:** Accepted  
**Date:** 2026-07-26

Scientific workflows expose typed results and neutral presentation contracts
such as `ReportTable`, `PlotCollection` and structured events. Rich,
Matplotlib, Dash, Plotly or notebook frontends translate those contracts for
their own medium.

This keeps progress, warnings, tables and figures consistent without parsing
terminal text or reverse-engineering arbitrary arrays.

## ADR-006 — Shared UI infrastructure is generic; scientific selection is module-specific

**Status:** Accepted  
**Date:** 2026-07-26

Forms, common inputs, matrices, messages, progress, tables, downloads, Plotly
presentation controls, workspaces, caches and jobs belong in reusable layers.

Module adapters and workflow packages decide which scientific options, report
families, plot families and downstream actions make sense for their domain. A
common visual language does not imply one identical workflow model for every
calculator.

## ADR-007 — The application is local-first and server-ready

**Status:** Accepted  
**Date:** 2026-07-26

The first supported mode is a local Dash server bound to a controlled loopback
address. The same pages and workflows should also run behind a WSGI server
without being rewritten.

For that reason the application uses a factory, configuration objects, URL
prefix support, a WSGI entry point and replaceable backend services rather than
page-level assumptions about one process or one user.

## ADR-008 — Browser state remains lightweight and opaque

**Status:** Accepted  
**Date:** 2026-07-26

Browser stores may contain identifiers and small interface choices such as
`workspace_id`, `job_id`, `result_id`, the selected view and presentation
preferences.

They may not contain complete scientific results, large arrays, open HDF5
objects, calculators, EOS sessions, server paths, credentials or private
server configuration.

## ADR-009 — Workspaces and file access are controlled server-side

**Status:** Accepted  
**Date:** 2026-07-26

Uploaded and generated files live below a workspace root managed by the
application. Browser input is never interpreted as an arbitrary server path.

The workspace service validates opaque identifiers, prevents traversal,
sanitizes display names, checks supported file types and sizes, publishes files
atomically and removes or expires resources through controlled operations.

## ADR-010 — Execution, cache, result storage and workspace services are replaceable

**Status:** Accepted  
**Date:** 2026-07-26

Execution, artifact caching, result storage and workspace management are
defined behind protocols. The initial local implementations are useful defaults,
not assumptions that callbacks or pages may depend on.

This leaves room for process workers, Redis, shared storage, databases or object
storage when server deployment requires them.

## ADR-011 — Native Quantas HDF5 is the persistence boundary

**Status:** Accepted  
**Date:** 2026-07-26

Native Quantas HDF5 files and archives are the authoritative persisted
scientific objects used by the library, CLI and GUI. CSV, text and image files
are derived exports.

Reopening a result must preserve provenance and stored precision. The GUI does
not replace HDF5 with browser JSON, and EOS keeps its own archive semantics.

## ADR-012 — Plotly and Dash AG Grid are GUI renderers, not scientific backends

**Status:** Accepted  
**Date:** 2026-07-26

Quantas GUI uses Plotly for interactive figures and Dash AG Grid for scientific
tables. Rich and Matplotlib remain presentation technologies of Quantas.

Plotly and grid options control appearance and interaction only; the scientific
values and conventions come from Quantas.

## ADR-013 — Visual transforms are distinct from scientific transforms

**Status:** Accepted  
**Date:** 2026-07-26

The interface must make clear whether an action changes only the view or changes
the science. Examples include camera rotation versus physical tensor rotation,
hiding a trace versus filtering data, changing a colormap versus transforming
values, and formatting precision versus stored precision.

Scientific transformations always pass through an appropriate public Quantas
operation.

## ADR-014 — Result construction is lazy and cacheable

**Status:** Accepted  
**Date:** 2026-07-26

Opening a result creates only a lightweight overview and inventory. Report and
plot families are built after the user selects them and are cached server-side.
Tables use virtualization, and suitable dense Cartesian traces may use WebGL.

Cosmetic changes must reuse the cached scientific object rather than reopening
HDF5 or rerunning a plot builder. Closing a result invalidates its cache
namespace.

## ADR-015 — EOS remains session-oriented and structurally separate

**Status:** Accepted  
**Date:** 2026-07-26

EOS is a persistent fitting session with editable datasets, fit attempts,
accepted and rejected candidates, diagnostics and archive history. It should not
be forced into the one-input/one-run/one-result model used by most other
modules.

The generic Result Explorer may inspect an archive, but the complete EOS
workflow belongs to its own page.

## ADR-016 — Scientific forms are declarative and validated in layers

**Status:** Accepted  
**Date:** 2026-07-26

Workflow forms are described by reusable schemas rather than built as large
page-specific blocks of Dash components.

Validation happens in four stages: component constraints, GUI structural and
cross-field checks, workflow-adapter construction, and final validation by the
public Quantas input and option types. Exact scientific values use suitable
numeric controls rather than imprecise sliders chosen for convenience.

## ADR-017 — The CLI is an audit reference, not a GUI runtime dependency

**Status:** Accepted  
**Date:** 2026-07-26

The CLI is useful when reviewing available options, defaults and terminology.
The GUI does not import Click command objects, invoke commands or parse terminal
output at runtime.

CLI audits can reveal missing controls, but GUI schemas are maintained against
the public API and the actual scientific meaning of each field.

## ADR-018 — Appearance settings are presentation-only and browser-local

**Status:** Accepted  
**Date:** 2026-07-26

Theme, typography scale, reduced motion and table density are saved in the
browser and affect only presentation. Supported theme modes are Quantas Dark,
Quantas Light and the operating-system preference.

These preferences never enter scientific requests, HDF5 files or numerical
exports.

## ADR-019 — Dash component compatibility is versioned and tested explicitly

**Status:** Accepted  
**Date:** 2026-07-26

During the alpha phase, Dash, Dash AG Grid and Plotly use exact tested versions
in `pyproject.toml` and `constraints/ui-baseline.txt`.

Compatibility is checked through constructor and callback-property audits,
active and disabled UI Kit states, complete layout serialization and
`tools/audit_dash_components.py`. A component is not considered compatible
merely because one page happens to render.

## ADR-020 — Responsive, accessible and cross-platform behaviour is part of completion

**Status:** Accepted  
**Date:** 2026-07-26

A feature is not complete after a desktop layout appears. Shared components and
workflows are reviewed on desktop, tablet and narrow mobile viewports, in both
themes, with keyboard focus, disabled states, readable text, reduced motion,
errors and warnings.

Windows, Linux and macOS installation and runtime behaviour are also part of
the acceptance criteria when applicable.

## ADR-021 — Public versions follow capability milestones

**Status:** Accepted  
**Date:** 2026-07-26

Public minor versions correspond to complete user-facing capabilities:

```text
0.1  Application foundation
0.2  Result Explorer
0.3  Elasticity
0.4  SEISMIC
0.5  HA/QHA
0.6  Thermoelasticity
0.7  EOS
0.8  Interoperability
0.9  Integrated beta validation
1.0  First stable release
```

Patch and pre-release identifiers may be used within a milestone. Later work
should not destabilize the current milestone merely to demonstrate future
features.

## ADR-022 — The default branch is protected and changes flow through pull requests

**Status:** Accepted  
**Date:** 2026-07-27

After the repository foundation was established, normal changes moved to
short-lived branches and pull requests. The default branch requires the project
CI gate, resolved conversations and a clean merge path.

Direct pushes, force pushes and branch deletion are not part of normal
maintenance. Squash merging keeps the development history readable for a
small-maintainer project.

## ADR-023 — CI uses least privilege and immutable action references

**Status:** Accepted  
**Date:** 2026-07-27

GitHub Actions receive only the permissions they need, and third-party actions
are pinned to immutable commit SHAs rather than moving tags.

Dependency review, code quality, tests, package checks and the aggregate gate
remain explicit. This reduces supply-chain risk and makes a passing commit more
reproducible.

## ADR-024 — Plotly preserves the scientific visual semantics of Quantas plots

**Status:** Accepted  
**Date:** 2026-07-27

Plotly figures should carry the same scientific meaning as figures rendered by
Quantas from the same public plot specification. Axes, units, masks, branch
identity, polarizations, color semantics, reference lines and dimensionality
must be preserved.

Interactive controls may improve exploration, but they must not silently change
the underlying data or interpretation. Validation compares Plotly and the
current Quantas Matplotlib rendering of the same public specification.

## ADR-025 — Quantas is required and compatibility is capability-based

**Status:** Accepted  
**Date:** 2026-07-28

Quantas is a required runtime dependency, not an optional plugin. At startup the
GUI checks both the supported version range and the public capabilities needed
by the current feature set.

If the backend is missing or incomplete, the application starts in a clear
shell-only degraded mode instead of failing halfway through an upload or
calculation. Result Explorer readiness and workflow readiness are reported
separately.

## ADR-026 — Public lifecycle inventories are the scientific discovery boundary

**Status:** Accepted  
**Date:** 2026-07-28

The GUI discovers available reports, plots, exports and valid contexts through
public lifecycle inventories exposed by each Quantas module.

Adapters may organize and label those inventories for the interface. They may
not inspect private result payloads or maintain a parallel scientific catalogue
that can drift from the backend.

## ADR-027 — Scientific plot selections are explicit and inventory-driven

**Status:** Accepted  
**Date:** 2026-07-29

Property, independent variable, fixed coordinate, representation and other
scientific plot choices are explicit values selected from the public inventory.
They form a typed `PlotBuildSelection` and a canonical cache fingerprint.

Presentation controls such as colormap, camera, hover mode and legend
visibility remain separate. Changing appearance must not rebuild the scientific
plot family.

## ADR-028 — Completed workflows hand off opaque result references to the shared Explorer

**Status:** Accepted  
**Date:** 2026-07-30

A workflow writes its native result into a controlled workspace, registers the
result with `ResultExplorerService`, stores only the returned opaque reference
and summary in browser state, and navigates to the Result Explorer.

Workflow pages do not duplicate the full report and plot interface. Uploaded
results use disposable Explorer-owned workspaces, while workflow results remain
owned by their workflow workspace.

## ADR-029 — Result access and artifact construction are concurrency-coordinated

**Status:** Accepted  
**Date:** 2026-07-30

Workspace access uses portable cross-process locks so that one worker cannot
delete a result while another is reading it. Uploads and exports are published
atomically.

Artifact construction is single-flight inside each process. Cache namespaces
carry invalidation state so that a builder finishing after close cannot put a
stale artifact back into the cache.

## ADR-030 — Long workflows run outside HTTP callbacks with persistent job state

**Status:** Accepted  
**Date:** 2026-07-30

Scientific calculations that may run for a long time are submitted to an
`ExecutionBackend`; they are not executed inside Dash request callbacks.
Browser state keeps only a job handle and event cursor, while status, progress,
messages, cancellation state and the result identifier live in a persistent job
store.

The first local implementation will use a separate process. Server deployments
must provide a queue and store shared by all WSGI workers behind the same
contract.

## ADR-031 — The Scientific UI Kit is an isolated application profile

**Status:** Accepted  
**Date:** 2026-07-30

The Scientific UI Kit remains part of the development package because it is
valuable for component, theme, disabled-state, accessibility and Dash-version
testing. It is not a scientific page for end users.

`quantas-gui --ui-kit` starts a separate profile containing the component
gallery, Settings and About. The standard WSGI application never exposes it.

---

## Deliberately unresolved choices

The project has not yet selected:

- the shared server worker and queue technology;
- a shared artifact-cache implementation;
- authentication and authorization technology;
- multi-user workspace ownership, quotas and retention;
- object storage versus a shared filesystem;
- a general node-based workflow editor;
- the final public hosting platform.

These choices should remain behind the accepted interfaces until a milestone
has enough real requirements to evaluate them properly.
