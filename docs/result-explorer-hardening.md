# Result Explorer hardening

This note records the boundaries that keep the Explorer maintainable as the
first executable workflows are added.

## Responsibility map

- Page modules expose routes and high-level layout.
- Components build passive interface sections.
- Callback modules connect user actions to services.
- `ResultExplorerService` owns the active result lifecycle.
- `QuantasResultBackend` calls public Quantas operations.
- Module adapters organise scientific families and selections.
- Table and Plotly renderers translate neutral contracts.
- Workspace and cache services manage files and expensive artifacts.

Callbacks should remain orchestration code. They should not open HDF5 directly,
recreate scientific inventories or contain renderer-specific scientific logic.

## Active result contract

The application shell contains one global active-result store. It holds an
opaque `ResultReference` and a small `ResultSummary`. A page must not create a
second competing store or serialize the native result.

Browser uploads create Explorer-owned disposable workspaces. Completed
workflows register an existing controlled result and retain ownership of their
workspace.

## Scientific and presentation state

Scientific selections determine which public PlotSpec Quantas builds. They are
explicit, validated and part of the artifact cache key.

Presentation controls modify only the Plotly rendering of that cached spec. The
interface shows when a scientific selection has changed and requires rebuilding,
and it offers separate reset actions for science and appearance.

## Renderer scope

The renderer preserves data, units, axes, masks, branch identity, annotations
and scientific meaning. It may translate colors, line styles, labels and layout
for Plotly. It may not alter calculations or infer missing semantics.

The central dispatcher may be split into family modules as it grows, but public
imports and figure behaviour should remain stable and covered by tests.

## Repeatable validation

The milestone needs small deterministic results or generators for every module.
Tests should cover public inventories, tables, plots, downloads, cache behaviour
and concurrent close. Manual validation should compare representative figures
with the current Quantas reference rendering.

## Concurrent close and construction

Closing a result invalidates its cache generation before deleting files. A
builder that started earlier may return to its own request, but it cannot
reinsert the artifact. Workspace deletion waits for readers and blocks new
leases after closing begins.
