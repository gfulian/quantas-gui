# Quantas GUI architectural decisions

This document records durable architectural decisions for the coordinated
development of Quantas and Quantas GUI.

A decision belongs here when it constrains future implementation across more
than one feature or milestone. Temporary implementation notes, unresolved
questions, and current bugs belong in [PROJECT_STATE.md](PROJECT_STATE.md) or an
issue tracker.

## Decision status

- **Accepted** — current project rule; new work must follow it.
- **Superseded** — retained for history but replaced by another decision.
- **Proposed** — not yet binding.

Changes to an accepted decision must explain the scientific, engineering, and
migration consequences and identify the decision that supersedes it.

## Decision index

| ID | Decision | Status |
|---|---|---|
| ADR-001 | Current and legacy source hierarchy | Accepted |
| ADR-002 | Quantas GUI is an independent package | Accepted |
| ADR-003 | The GUI depends only on the public Quantas API | Accepted |
| ADR-004 | Scientific and presentation responsibilities remain separate | Accepted |
| ADR-005 | Quantas emits frontend-neutral results, reports, plots, and events | Accepted |
| ADR-006 | Shared UI infrastructure is generic; scientific selection is module-specific | Accepted |
| ADR-007 | The application is local-first and server-ready | Accepted |
| ADR-008 | Browser state remains lightweight and opaque | Accepted |
| ADR-009 | Workspaces and file access are controlled server-side | Accepted |
| ADR-010 | Execution, cache, result storage, and workspace services are replaceable | Accepted |
| ADR-011 | Native Quantas HDF5 is the persistence boundary | Accepted |
| ADR-012 | Plotly and Dash AG Grid are GUI renderers, not scientific backends | Accepted |
| ADR-013 | Visual transforms must not be confused with scientific transforms | Accepted |
| ADR-014 | Result construction is lazy and cacheable | Accepted |
| ADR-015 | EOS remains session-oriented and structurally separate | Accepted |
| ADR-016 | Scientific forms are declarative and validated in layers | Accepted |
| ADR-017 | The CLI is an audit reference, not a GUI runtime dependency | Accepted |
| ADR-018 | Appearance settings are presentation-only and browser-local | Accepted |
| ADR-019 | Dash component compatibility is versioned and tested explicitly | Accepted |
| ADR-020 | Responsive, accessible, cross-platform behaviour is part of completion | Accepted |
| ADR-021 | Public versions follow capability milestones | Accepted |

---

## ADR-001 — Current and legacy source hierarchy

**Status:** Accepted

**Date:** 2026-07-26

### Decision

The Quantas `dev-refactor` line is the current authority for scientific
behaviour, architecture, public API, tests, and native formats.

Quantas `0.9.1` is retained only for:

- historical behaviour;
- conceptual compatibility;
- legacy input and output formats;
- numerical comparison where explicitly required.

The most recent approved Quantas GUI repository or source snapshot is the
authority for the GUI.

### Consequences

- legacy code must not be copied automatically into the refactored architecture;
- conflicts are resolved in favour of current code and tests, with the conflict
  reported explicitly;
- historical behaviour is preserved only when intentionally required and
  documented.

---

## ADR-002 — Quantas GUI is an independent package

**Status:** Accepted

**Date:** 2026-07-26

### Decision

The graphical application is distributed separately as:

```text
Distribution: quantas-gui
Python package: quantas_gui
Launcher: quantas-gui
```

Quantas remains a standalone scientific library and command-line application.

### Consequences

- Dash, Plotly, browser state, web deployment, and GUI assets do not become
  dependencies of Quantas;
- Quantas GUI can evolve and release on its own roadmap;
- both packages can be installed into the same virtual environment during
  development.

---

## ADR-003 — The GUI depends only on the public Quantas API

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Runtime scientific integration must use `quantas.api`, including public module
namespaces, the registry, rendering contracts, profiles, and interoperability
functions.

The GUI must not depend directly on:

- `quantas.cli`;
- `quantas.modules`;
- private calculators or internal I/O implementations;
- Rich or Matplotlib renderers;
- terminal output parsing.

### Consequences

- CLI and GUI remain separate frontends of the same backend;
- private refactoring in Quantas does not require a GUI rewrite while the public
  contract remains stable;
- missing public capability must be added deliberately to `quantas.api`, not
  bypassed through an internal import.

---

## ADR-004 — Scientific and presentation responsibilities remain separate

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Quantas owns:

- formulas, methods, tolerances, conventions, units, and precision;
- typed scientific input, options, and results;
- numerical validation and calculation;
- native persistence and scientific interoperability.

Quantas GUI owns:

- forms and preliminary structural validation;
- application orchestration and job presentation;
- tables, interactive figures, layout, themes, and exports of supported views;
- session navigation and user interaction.

### Consequences

The GUI must never alter scientific behaviour merely to simplify a component or
improve a figure.

---

## ADR-005 — Quantas emits frontend-neutral results, reports, plots, and events

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Scientific workflows expose frontend-neutral contracts such as typed results,
`ReportTable`, `PlotCollection`, and structured events. Frontends translate
these contracts into Rich/Matplotlib, Dash/Plotly, notebook, or other
presentations.

### Consequences

- the GUI does not reconstruct scientific meaning by inspecting arbitrary
  arrays when a public report or plot specification exists;
- progress, warnings, errors, and results can be presented consistently without
  parsing terminal strings;
- renderer-specific options remain outside scientific payloads.

---

## ADR-006 — Shared UI infrastructure is generic; scientific selection is module-specific

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Reusable meaning belongs in shared layers:

- forms and common inputs;
- matrices and repeatable grids;
- progress, logs, warnings, and errors;
- table rendering and CSV export;
- Plotly dispatch and cosmetic controls;
- upload, download, cache, workspace, and job infrastructure.

Module-specific packages or adapters decide:

- which scientific options are meaningful;
- which report and plot families are available;
- how scientific content is grouped and labelled;
- which transformations or downstream actions are valid.

### Consequences

A common visual style does not imply an identical workflow model for every
scientific module.

---

## ADR-007 — The application is local-first and server-ready

**Status:** Accepted

**Date:** 2026-07-26

### Decision

The initial application runs locally on a controlled loopback address and opens
in a browser. The architecture must nevertheless support later laboratory or
public server deployment without rewriting pages or scientific workflows.

The application therefore uses:

- an application factory;
- configuration objects;
- a WSGI entry point;
- URL-prefix support;
- backend protocols rather than page-level process assumptions.

### Consequences

Local shortcuts that prevent multi-user or multi-process operation are not
accepted, even when they would make an early prototype simpler.

---

## ADR-008 — Browser state remains lightweight and opaque

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Browser storage may contain only lightweight interface state and opaque
identifiers such as:

```text
workspace_id
job_id
result_id
selected view
presentation preferences
```

It must not contain:

- large numerical arrays;
- complete scientific results;
- open HDF5 objects;
- active calculators or EOS sessions;
- server filesystem paths;
- credentials or private deployment state.

### Consequences

Large objects remain in controlled server-side services and are reconstructed
or retrieved by identifier.

---

## ADR-009 — Workspaces and file access are controlled server-side

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Uploaded and generated files live beneath a workspace root managed by the
application. Browser input is never interpreted as an arbitrary server path.

Workspace services must:

- validate opaque identifiers;
- prevent traversal;
- sanitize display names;
- validate supported upload types and sizes;
- write uploads atomically;
- delete or expire resources through controlled operations.

### Consequences

A future server can add user ownership and quotas without changing the page
contract.

---

## ADR-010 — Execution, cache, result storage, and workspace services are replaceable

**Status:** Accepted

**Date:** 2026-07-26

### Decision

The following concerns are defined behind interfaces or protocols:

- execution backend;
- artifact cache;
- result store;
- workspace manager.

The initial local implementations must not be assumed by callbacks or pages.

### Consequences

Local process/disk implementations can later be replaced by queued workers,
Redis, shared storage, databases, or object storage without changing scientific
forms and renderers.

No specific server technology is accepted yet merely because an interface has
been prepared for it.

---

## ADR-011 — Native Quantas HDF5 is the persistence boundary

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Native Quantas HDF5 results and archives remain the authoritative persisted
scientific objects used by CLI, API, and GUI.

CSV, plain text, images, and other downloads are derived exports, not canonical
state.

### Consequences

- reopening a result must preserve provenance and scientific precision;
- the GUI must not replace HDF5 with browser JSON;
- EOS archives retain their own persistent record and session semantics.

---

## ADR-012 — Plotly and Dash AG Grid are GUI renderers, not scientific backends

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Quantas GUI uses:

- Plotly for interactive scientific figures;
- Dash AG Grid for interactive scientific tables.

Matplotlib and Rich remain presentation technologies of Quantas and are not GUI
runtime dependencies.

### Consequences

Plotly and grid options control interaction and appearance, while scientific
values and conventions remain those supplied by Quantas.

---

## ADR-013 — Visual transforms must not be confused with scientific transforms

**Status:** Accepted

**Date:** 2026-07-26

### Decision

The interface must distinguish explicitly between:

- rotating a Plotly camera and rotating a physical tensor or basis;
- hiding a trace and filtering scientific data;
- changing a colormap and transforming numerical values;
- changing displayed units and recomputing a scientific result;
- formatting precision and stored numerical precision.

### Consequences

Every scientific transformation must pass through an appropriate Quantas API
operation. Cosmetic controls may not mutate the original result.

---

## ADR-014 — Result construction is lazy and cacheable

**Status:** Accepted

**Date:** 2026-07-26

### Decision

The Result Explorer opens a file by constructing only a lightweight overview
and inventory. Expensive report and plot families are built only after the user
selects them and are cached server-side through an `ArtifactCache` contract.

Tables use virtualization, and compatible dense Cartesian traces may use
Plotly WebGL.

### Consequences

- changing a cosmetic control must not reopen HDF5 and rerun a scientific plot
  builder unnecessarily;
- closing a result invalidates its cache namespace;
- the current process-local cache can be replaced by a shared cache for server
  deployment.

---

## ADR-015 — EOS remains session-oriented and structurally separate

**Status:** Accepted

**Date:** 2026-07-26

### Decision

EOS is not forced into the generic one-input/one-run/one-result workflow used by
other calculators.

Its complete GUI must model:

- persistent datasets;
- editable inclusion state;
- fitting attempts;
- accepted and rejected fits;
- diagnostics;
- archive history and resumption.

The generic Result Explorer may inspect an EOS archive structurally, but the
full interactive workflow belongs to a dedicated EOS page.

### Consequences

Generic abstractions may be reused only where their semantics genuinely match
EOS.

---

## ADR-016 — Scientific forms are declarative and validated in layers

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Workflow forms are described through reusable schemas rather than handwritten
page-specific controls.

Validation occurs in layers:

1. browser/component constraints;
2. GUI structural coercion and cross-field validation;
3. workflow adapter construction;
4. final validation by public Quantas input and options contracts.

### Consequences

- reusable controls remain consistent across workflows;
- the GUI does not duplicate or replace scientific validation in Quantas;
- exact scientific values use appropriate numeric controls rather than
  imprecise sliders chosen for convenience.

---

## ADR-017 — The CLI is an audit reference, not a GUI runtime dependency

**Status:** Accepted

**Date:** 2026-07-26

### Decision

The Quantas CLI may be inspected during development to inventory options,
commands, defaults, and terminology. Quantas GUI must not import Click command
objects or invoke CLI commands at runtime.

### Consequences

- CLI audits help identify missing form-control families;
- GUI schemas are maintained against public API contracts and actual scientific
  meaning, not generated blindly from Click metadata;
- CLI and GUI remain independently testable frontends.

---

## ADR-018 — Appearance settings are presentation-only and browser-local

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Theme, typography scale, reduced-motion preference, and table density are stored
locally in the browser and affect only presentation.

The supported theme modes are:

- Quantas Dark, the default;
- Quantas Light;
- operating-system preference.

### Consequences

Appearance preferences are never written into scientific requests, HDF5
results, or numerical exports. Plotly and Dash AG Grid must follow the effective
theme consistently.

---

## ADR-019 — Dash component compatibility is versioned and tested explicitly

**Status:** Accepted

**Date:** 2026-07-26

### Decision

During the alpha phase, Dash, Dash AG Grid, and Plotly use an exact compatibility
baseline declared in `pyproject.toml` and `constraints/ui-baseline.txt`.

Component properties must be checked against the installed versions through:

- static property contracts;
- constructor and callback-property audits;
- complete UI Kit construction in active and disabled states;
- serialization of the application and lazy page layouts;
- `tools/audit_dash_components.py` in the real target environment.

### Consequences

A component is not considered compatible merely because its page source imports
or its layout appears partially.

---

## ADR-020 — Responsive, accessible, cross-platform behaviour is part of completion

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Desktop layout is not the sole acceptance target. Shared components and
workflows must be reviewed for:

- desktop, tablet, and narrow mobile viewports;
- Quantas Dark and Quantas Light;
- keyboard focus and disabled states;
- readable text scaling;
- reduced motion;
- warnings and errors;
- Windows, Linux, and macOS installation and runtime behaviour.

### Consequences

Mobile readiness, accessibility, and alternate themes are not deferred cosmetic
work. They are part of milestone completion when applicable.

---

## ADR-021 — Public versions follow capability milestones

**Status:** Accepted

**Date:** 2026-07-26

### Decision

Public minor versions represent user-visible capability milestones:

```text
0.1  Application foundation
0.2  Result Explorer
0.3  Elasticity
0.4  SEISMIC
0.5  HA/QHA
0.6  Thermoelasticity
0.7  EOS
0.8  Interoperability
0.9  Integration and beta validation
1.0  First stable release
```

Patch and pre-release identifiers may be used within a milestone, for example
`0.2.1a2`.

### Consequences

- work from a later milestone should not destabilize completion of the current
  one;
- a milestone is complete only when its user-visible capability, tests,
  persistence, documentation, and scientific equivalence criteria are met;
- version `1.0` includes first stable publication on PyPI.

---

## Deliberately unresolved architecture

The following topics are not yet accepted decisions:

- the local background-job implementation;
- Celery/Redis or another server worker and cache stack;
- authentication and authorization technology;
- multi-user workspace ownership and retention policy;
- object storage versus shared filesystem;
- a general node-based interoperability editor;
- public hosting and operational deployment platform.

They must remain behind the accepted interfaces until evaluated in the
appropriate roadmap milestone.
