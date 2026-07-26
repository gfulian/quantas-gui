# Results Explorer performance policy

The Results Explorer treats expensive scientific construction and browser
presentation as different costs.

## Local alpha policy

- Opening a result builds only a lightweight overview and payload inventory.
- Report and plot *families* are listed before their content is built.
- One selected family is constructed on demand.
- Overview objects, family descriptors, report tables, and PlotCollections are
  retained in a bounded process-local LRU cache.
- Closing a result invalidates its entire cache namespace.
- The browser stores only opaque result references and bounded plot inventory.
- Tables use Dash AG Grid so row rendering is virtualized by the grid rather
  than creating one DOM element for every cell.
- Cartesian dense traces use Plotly WebGL traces where the public specification
  permits them.
- Plotly `uirevision` preserves zoom, camera, and selections while cosmetic
  controls update the figure.

The local cache is intentionally behind an `ArtifactCache` protocol. A server
installation may replace it with a shared Redis/filesystem implementation
without changing pages or scientific adapters.

## Diagnostics

`QUANTAS_GUI_RESULT_CACHE_ENTRIES` controls the local cache size (default 48).
The optional `performance` extra installs `orjson`, which Dash can use for
faster JSON serialization when available.

Avoid timing assertions in unit tests. Regression tests instead verify that
repeated requests call the scientific builder once and return the same cached
artifact.
