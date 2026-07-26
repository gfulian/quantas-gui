# Module-aware Results Explorer adapters

The generic Results Explorer owns upload policy, opaque references, caching,
tables, Plotly dispatch, messages, and bounded data views. Scientific selection
belongs to small adapters under `quantas_gui.explorer.adapters`.

```text
ResultExplorerService
    ↓ cached ResultOverview / families / artifacts
QuantasResultBackend
    ↓ public quantas.api namespace only
ResultModuleAdapter
    ├── report families
    ├── plot families
    ├── module-specific builders
    └── presentation grouping
```

Adapters never import `quantas.modules`, Click, Rich, Matplotlib, or internal
renderers. They call only the namespace returned by the public registry.

## Current scientific families

| Module | Report families | Plot families |
|---|---|---|
| Elasticity | neutral report | stored 2D polar; on-demand 3D directional surfaces |
| SEISMIC | standard; extended; debug | spherical maps; extrema summary; 3D wave surfaces |
| HA | neutral report | thermodynamic curves |
| QHA | neutral report | one-dimensional curves; P-T contours when the archive contains a grid |
| Thermoelasticity | standard; extended; debug | elastic-volume fits; P-T maps; calibration domain; profiles |
| EOS | structural archive summary | none in the generic Explorer |

EOS remains session-oriented because a plot belongs to a selected dataset and
accepted fit record rather than to the archive as a whole.

## Placement rule

A feature belongs in the generic layer when its meaning does not depend on the
scientific module: CSV generation, table virtualization, colormaps, hover,
camera presets, visibility toggles, loading state, and cache policy.

A feature belongs in a module adapter when it chooses scientific content:
which report level is meaningful, whether a P-T contour is available, which
profile is selected, or whether a 3D surface must be calculated on demand.
