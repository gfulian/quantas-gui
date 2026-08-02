# Quantas backend lifecycle

The current GUI requires Quantas `>=2.0.0b8,<2.1` and uses only public objects
under `quantas.api`.

## Startup compatibility check

At application startup, the service layer builds an immutable compatibility
record. The check covers:

- installed Quantas version;
- import of `quantas.api`;
- the public registry and expected module descriptors;
- result identification and reopening;
- report, plot inventory, plot building, export and persistence operations;
- public PlotSpec and inventory types;
- workflow operations such as `read_input`, `normalize_input`, `run` and
  `write_result` when an executable workflow needs them.

Result Explorer readiness and workflow readiness are separate. A backend may be
able to open old results without yet exposing everything needed to launch a new
calculation.

## Degraded mode

When compatibility fails, the application keeps Home, About, Settings and the
backend diagnostics available. Scientific pages and controls are disabled.
Uploads are rejected before Base64 decoding, workspace creation or file writes.

This is preferable to allowing an apparently healthy application to fail in the
middle of a scientific action.

## Opening a result

```text
controlled result path
        ↓
registry.module_from_result(path)
        ↓
registry.open_result(path)
        ↓
module.build_report(result)
module.describe_plots(result)
module.build_plots(result, selection)
        ↓
AG Grid and Plotly
```

Opening the file creates only a lightweight overview and inventory. Reports and
plots are built lazily and cached using a fingerprint of the scientific
selection. Cosmetic Plotly changes reuse the cached PlotSpec.

## Exports and input generation

Scientific exports and input generators are used only when the module advertises
them publicly. The GUI does not duplicate file formats or convert a result by
reading private HDF5 groups.

## EOS

EOS archives follow their own public persistence and record-selection API. The
generic Explorer treats them as read-only persistent archives. The complete
editing and fitting session belongs to the dedicated EOS workflow.

## Concurrent access

Every public result operation runs while holding the workspace read lease. A
close operation marks the workspace as closing, waits for active readers,
invalidates cached artifacts and then removes Explorer-owned files. Workflow-
owned results keep their workspace after the Explorer view is closed.
