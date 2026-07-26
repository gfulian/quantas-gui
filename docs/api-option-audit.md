# Public Quantas API option audit

The CLI inventory is checked against the passive option classes exported by
`quantas.api`. These public dataclasses are the authoritative objects that GUI
workflow adapters must construct.

## Elasticity

- calculation toggles for 2D and 3D data;
- angular sampling counts;
- nested 3D surface options with property selection and batch size;
- optional physical tensor rotation.

Recommended controls: switches, integer inputs, checklist or multi-select,
advanced batch-size input, and a three-angle/vector rotation editor.

## SEISMIC

- spherical grid and hemisphere;
- calculation level from phase through enhancement;
- polarization tracking;
- several relative and absolute numerical tolerances;
- plot properties, projection, colormap, contour levels, surface geometry,
  wave modes, surface families, and polarization presentation.

Recommended controls: radio or select for hemisphere/level, exact integer
inputs for grid size, scientific-number inputs for tolerances, grouped advanced
sections, and reusable plotting selectors.

## HA and QHA

- exact temperature and pressure domains;
- energy, volume, frequency, temperature, and pressure units;
- polynomial and EOS choices;
- numerical derivative controls;
- diagnostics, uncertainty estimation, Monte Carlo settings, failure policies,
  extrapolation policies, Grüneisen options, and thermal-expansion method;
- contour and Dulong–Petit plotting controls.

Recommended controls: range-triplet composites for state domains, unit
selectors, policy selectors with explanations, nested advanced sections, exact
scientific-number inputs, and dependency rules that reveal uncertainty controls
only when uncertainty estimation is enabled.

## EOS

EOS is session-oriented. Its public surface includes fit requests, solver
options, parameter constraints, plotting options, reporting options, archive
record selection, calculation coordinates, and uncertainty propagation.

Recommended controls: dataset/record selectors, model and solver selectors,
editable parameter and bounds grids, repeatable P/T curve lists, checkboxes for
excluded data and uncertainty presentation, and a dedicated session state
rather than one flat form.

## Thermoelasticity

- reference EOS and finite-strain order;
- fitting method and iteration limits;
- extrapolation, fit-failure, quality, and stability policies;
- several quality thresholds;
- reference-EOS, volume, and adiabatic uncertainty propagation;
- P–T, profile, domain, fit-diagnostic, and comparison plot options;
- exactly-one fixed pressure/fixed temperature comparison coordinates.

Recommended controls: grouped policy selectors, scientific-number threshold
inputs, switches for propagation choices, component selectors, contour and
layout controls, and explicit cross-field validation.

## Consequence for the GUI

No module page should manually construct a wall of Dash components. Each page
should define a `FormSchema`, then use a small workflow adapter to translate the
validated values into the relevant public API dataclasses. Nested API option
objects become nested or collapsible form sections rather than flattened names.
