# Results Explorer

The Results Explorer is the shared scientific presentation surface of Quantas
GUI. It verifies the boundary from native HDF5 to public Quantas contracts,
module-aware scientific selection, frontend-neutral reports/plots, and
Dash/Plotly presentation.

## Boundaries

The Explorer may identify a result from persisted metadata, display provenance,
request public report/plot specifications, and apply visual interactivity. It
may not infer file type from names, import private Quantas modules, modify
scientific data, or place large arrays in browser storage.

```text
browser upload
    ↓ controlled workspace + opaque ResultReference
ResultExplorerService
    ↓ bounded ArtifactCache
QuantasResultBackend
    ↓ quantas.api.registry only
module ResultModuleAdapter
    ↓ selected report/plot family
ReportTable / PlotCollection
    ↓
Dash AG Grid / Plotly
```

## Module-aware lazy families

Opening a native result creates only `ResultOverview`. Entering Tables or Plots
lists lightweight families. Scientific content is built only after a family is
selected.

- Elasticity: archived 2D polar plots and on-demand 3D surfaces.
- SEISMIC: spherical maps, extrema summaries, and 3D wave surfaces.
- HA: harmonic thermodynamic curves.
- QHA: one-dimensional curves and P-T contours when a grid exists.
- Thermoelasticity: fits, P-T maps, domain diagnostics, and profiles according
  to the archived workflow stage.
- EOS: archive summary only; accepted-fit selection remains in the dedicated
  session UI.

See [module adapter architecture](module-result-adapters.md).

## Views

### Overview

Module identity, method, schema, provenance, warnings, events, and a payload
inventory containing only type, shape, dtype, and bounded metadata.

### Tables

A report-family selector builds one public `ReportTable` collection. Tables are
grouped using module presentation adapters and displayed with Dash AG Grid.
Formatting metadata is applied to separate display values; CSV export always
uses raw cells and unit-bearing headers.

### Plots

A scientific-view selector builds one plot family. A second selector lists its
figures with module grouping and descriptions. The generic dispatcher supports:

- line and error/band plots;
- contours and diagnostic masks;
- polar panels;
- 3D surfaces and vector layers;
- spherical maps and summaries;
- composed panels.

A collapsible responsive drawer shows only controls meaningful for the selected
specification: colormap, hover, projection, isolines, labels, surface opacity,
3D camera, colorbar, legend, grid, and axes. These controls affect display only.
`uirevision` preserves user zoom and camera where Plotly supports it.

### Messages and Data

Persistent events and warnings can be filtered by level and text. Metadata,
normalized input, options, and payload structure are exposed through bounded
JSON views; large arrays remain server-side.

## Performance

Prepared overviews, family inventories, report tables, and PlotCollections are
cached under `(workspace_id, result_id, artifact...)`. Repeated figure or table
selection therefore does not reopen HDF5 or rerun a scientific builder. Closing
a result invalidates the complete cache namespace.

The local implementation uses a bounded thread-safe LRU. The `ArtifactCache`
protocol permits a future Redis/filesystem implementation for multi-process
server deployment. See [performance policy](performance.md).
