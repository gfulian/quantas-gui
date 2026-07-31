# Architecture

Quantas GUI is deliberately thin in scientific terms. It coordinates the user
experience, but it does not reimplement Quantas.

## Dependency direction

```text
pages / callbacks / components / renderers
                     ↓
                 services
                     ↓
                 quantas.api
```

The GUI never drives the Click CLI, parses Rich output, consumes Matplotlib
figures as data, or imports private scientific modules. A missing capability is
a backend API problem to solve explicitly, not a reason to bypass the public
boundary.

## Scientific data flow

```text
public Quantas Input and Options
               ↓
       quantas.api workflow
               ↓
 result object + events + native HDF5
               ↓
 ReportTable / PlotCollection / exports
               ↓
       AG Grid / Plotly / downloads
```

The GUI may change presentation: colormaps, hover behaviour, camera position,
visible traces, layout and export format. It may not change formulas, units,
precision, masks, branch identity or scientific conventions.

## Result Explorer layers

The Explorer is split by responsibility:

- `pages/results.py` exposes the route;
- `components/` builds passive interface sections;
- `callbacks/result_*.py` connects Dash events;
- `services/results.py` coordinates the result lifecycle;
- `services/result_backend.py` talks to public Quantas operations;
- `explorer/adapters/` organises module-specific scientific choices;
- `renderers/` translates neutral tables and PlotSpecs;
- `services/workspaces.py` controls files and concurrent access.

The browser stores only an opaque result reference and lightweight summary.
Tables, plots, native results and HDF5 resources remain server-side and are
built when requested.

## From local use to a server

Pages and callbacks depend on service protocols rather than on one process or
one filesystem implementation. Long calculations are represented by job
handles and events and will run outside HTTP callbacks.

`0.3.0a2` provides the first complete process-backed workflow for Elasticity.
The worker uses only `quantas.api.elasticity`, persists job state and events in
the controlled workspace, and publishes the native HDF5 result atomically. The
Dash page depends on the execution descriptor and workflow service, not on the
local process implementation. A multi-worker server will use the same interface
with a shared queue and persistent job store; server mode does not reuse the
process-local registry and displays execution as unavailable until one is
injected.

## Workspace safety

All files live below a controlled workspace root. Browser values are never used
as arbitrary server paths. The local workspace implementation validates
identifiers, prevents traversal, writes atomically and coordinates reads,
exports and deletion with cross-process locks.

Artifact construction is single-flight within each process. Closing a result
invalidates its cache generation, so a late builder cannot restore an artifact
that belongs to a closed result.

## Backend compatibility

Startup checks the required Quantas version and the public capabilities needed
by the current GUI. If the backend is absent or incomplete, the application
starts in a clear shell-only mode and disables scientific navigation.

Available reports, plots, exports and contexts come from public lifecycle
inventories. Adapters may improve grouping and labels, but they do not infer
scientific availability from private payloads.
