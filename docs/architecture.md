# Architecture

## Dependency rule

```text
quantas_gui.pages / callbacks / components / renderers
                         ↓
                quantas_gui.services
                         ↓
                    quantas.api
```

Quantas GUI must never drive the Click CLI, parse Rich output, consume
Matplotlib figures, or import private scientific implementations.

## Frontend-neutral scientific flow

```text
Quantas input/options
        ↓
quantas.api workflow
        ↓
ResultData + events + HDF5
        ↓
ReportTable / PlotCollection
        ↓
Dash table renderer / Plotly renderer
```

The GUI may control presentation such as colormaps, hover templates, camera,
visibility, layout, and export. It must not change formulas, units, numerical
precision, masks, branch identity, or scientific conventions.

## Results Explorer layers

```text
pages/results.py
      ↓
components/result_shell.py
components/result_overview.py
components/result_renderers.py
components/renderer_controls.py
      ↓
callbacks/results.py
      ↓
services/results.py
services/result_backend.py
services/workspaces.py
      ↓
quantas.api.registry / quantas.api.rendering
```

The browser stores only a `ResultReference` and `ResultSummary`. Tables, plot
collections, native results, and HDF5 resources remain server-side and are
reconstructed lazily.

## Local-to-server seam

Pages submit opaque request identifiers to an `ExecutionBackend` and retain
only lightweight job and result identifiers in browser state. A local backend
can later be replaced by Celery/Redis without changing page workflows.

Large arrays, open HDF5 objects, active EOS sessions, and calculators must not
be serialized into `dcc.Store` or process-global variables.

## Workspace security

All uploaded and generated files live beneath a controlled workspace root.
Browser input must never be treated as a direct filesystem path. The initial
`LocalWorkspaceStore` validates opaque identifiers, prevents traversal, and
writes uploads atomically before Quantas attempts to inspect them.
