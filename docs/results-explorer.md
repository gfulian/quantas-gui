# Result Explorer

The Result Explorer is the common read-only interface for native Quantas
results. Users can upload a file, and future workflows can open their completed
result directly without uploading it again.

## What the Explorer is responsible for

The Explorer:

- identifies a result through `quantas.api.registry`;
- keeps the file in a controlled server-side workspace;
- shows provenance, inputs, options, warnings and events;
- asks the public module API which reports, plots and exports are available;
- builds expensive artifacts only after the user selects them;
- renders public `ReportTable` objects with Dash AG Grid;
- renders public PlotSpecs with Plotly;
- offers original-file, report, table and supported scientific downloads;
- closes Explorer-owned workspaces safely.

It does not calculate new scientific results, infer missing scientific meaning
from private payloads, or put large numerical objects in browser storage.

## Opening a file

Supported uploads use `.h5`, `.hdf5` or `.hdf`. Before decoding the browser
payload, the application checks that the Quantas backend is ready. The file is
then written atomically to an isolated workspace and opened through the public
registry.

The browser receives an `ActiveResultState` containing only an opaque reference
and a lightweight summary. The path, native result and HDF5 handle stay on the
server.

## Views

### Overview

Shows the module, source, creation information, provenance, normalized inputs,
options and a compact summary.

### Tables

The module advertises report families. A selected family is built lazily and
rendered with AG Grid. Raw numeric and boolean values are preserved for sorting
and filtering; formatting follows the precision and units supplied by Quantas.
CSV downloads contain the complete table, not only visible rows.

### Plots

The module exposes a public plot inventory. The GUI presents only the property,
independent variable, fixed coordinate, representation and other contexts listed
there. Those choices form a `PlotBuildSelection` and a stable cache key.

After the public PlotSpec is built, presentation controls can change colormap,
line appearance, hover mode, legend, grid, contour presentation, projection,
opacity or camera without rebuilding the scientific object.

### Messages

Stored warnings and structured events can be filtered by severity and text.
Technical exceptions are logged server-side; the browser receives a bounded,
sanitized message without local paths.

### Data

A bounded technical view helps diagnose file structure without transferring
complete arrays. Large mappings, sequences, strings and arrays are summarized.
Server paths are reduced to safe display names.

## Module behaviour

Elasticity, SEISMIC, HA, QHA and Thermoelasticity use module adapters that group
public lifecycle families and provide interface labels. These adapters do not
recreate calculations or inspect private backend internals.

EOS is different. Its native object is a persistent archive with datasets, fit
slots and records. The Explorer offers read-only archive, record, status,
parameter, covariance and diagnostic-plot inspection. Editing and fitting are
reserved for the dedicated EOS workflow.

## Caching and performance

Opening a file is intentionally cheap. Report and plot families are built on
demand and cached by workspace, result, family and scientific selection.
Cosmetic changes reuse the same artifact.

Tables use AG Grid virtualization. Suitable dense Cartesian traces may use
Plotly WebGL. Cache size is bounded by configuration and remains process-local
in the current server implementation.

## Concurrent requests and close

Workspace locks coordinate reads and deletion across processes. If a result is
closed while a report or plot is being built, the active request may finish,
but its artifact cannot return to the invalidated cache. Explorer-owned files
are removed after active readers release the workspace.

Workflow-owned results use the same Explorer but keep their workspace when the
view is closed.

## Backend unavailable behaviour

When Quantas is missing or incompatible, the Results page and upload controls
are disabled and the application shows backend diagnostics. No upload data are
decoded or written in that state.

## Validation

A Result Explorer change should be checked with representative results from
each module. Validation includes:

- public inventory and selector correctness;
- table values, units, formatting, sorting and CSV output;
- Plotly/Matplotlib scientific equivalence where applicable;
- cache reuse and invalidation;
- warnings, errors and empty states;
- dark and light themes;
- desktop and narrow viewports;
- keyboard operation;
- large-result performance.

## SEISMIC three-dimensional surfaces

SEISMIC exposes two intentionally overlapping three-dimensional families.

**General scalar-field surface** presents one or more sampled scalar properties
on a unit sphere or, where Quantas defines one, on the property's natural
physical carrier. It is the preferred family for directional anisotropy, shear
splitting, P-to-S velocity ratios, power-flow angle and enhancement. Phase and
group velocities remain available because they are valid scalar fields, but the
shape and the colour may then carry different quantities.

**Acoustic wave surface** presents the canonical phase-velocity, slowness or
group-wavefront surface for the selected P, S1 or S2 mode. This is the clearest
choice when the scientific question concerns the physical acoustic surface
itself.

Both families are built lazily. The scalar selector accepts several properties
in one build; the acoustic selector accepts several surface types and modes.
After that build, the figure selector switches among the cached PlotSpecs
without rerunning SEISMIC or rebuilding the scientific collection. The scalar
family defaults to one property so that opening a dense result does not create a
large collection unexpectedly.
