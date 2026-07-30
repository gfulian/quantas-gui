# Performance policy

The alpha aims for responsive local use without hiding expensive scientific
work in the browser.

## Current approach

- Opening a result builds only its overview and public inventories.
- Reports and plots are constructed when selected.
- Artifacts are cached by result, family and scientific selection.
- Appearance changes reuse cached PlotSpecs.
- AG Grid virtualizes large tables.
- Compatible dense Cartesian traces may use WebGL.
- Browser stores contain identifiers and small preferences, not numerical
  payloads.
- Cache size is bounded and configurable.

## What to measure

Performance work should use representative native files rather than synthetic
DOM-only tests. Record:

- result-open time;
- first and cached report-build time;
- first and cached plot-build time;
- table row and column counts;
- Plotly trace and point counts;
- browser responsiveness during selection and appearance changes;
- server memory before and after close;
- workspace cleanup time;
- behaviour with simultaneous requests.

## Practical thresholds

No single timing threshold fits every scientific result, but a change should not
make routine interactions noticeably slower without a documented reason. Slow
scientific construction should be visible as progress and should not block
unrelated HTTP requests once workflow execution is enabled.

When a dataset is too large for a current renderer, report the limitation and
choose a scientifically safe reduction strategy through Quantas. Do not silently
truncate or resample data in the GUI.
