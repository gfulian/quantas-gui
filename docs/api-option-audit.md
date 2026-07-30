# Audit of the public Quantas API options

This document maps the public Quantas options to the controls that will be
needed in the GUI. The CLI remains useful as a completeness check, but workflow
forms must ultimately construct objects from `quantas.api`: that is the real
runtime contract with the backend.

## Elasticity

The current contract covers 2D and 3D result generation, angular sampling,
three-dimensional surface options and optional physical rotation of the elastic
tensor.

These choices map naturally to switches, exact integer fields, a property
selection and an explicit rotation editor. Physical tensor rotation must remain
clearly separate from moving the Plotly camera.

## SEISMIC

SEISMIC exposes a broader configuration surface: spherical grid, hemisphere,
calculation level, polarization tracking, numerical tolerances and several
presentation choices.

Discrete choices can use radio buttons or dropdowns. Grid sizes and tolerances
need exact numeric fields. Less common settings should be collected in an
advanced section without hiding their scientific meaning.

## HA and QHA

HA and QHA require exact temperature and pressure domains, units, fitting or
interpolation methods, diagnostics, failure policies and optional uncertainty
propagation.

The most useful shared controls are:

- exact `start / stop / step` fields for temperature and pressure;
- unit and method selectors;
- advanced sections for diagnostics and Monte Carlo settings;
- dependency rules that reveal uncertainty controls only when uncertainty
  estimation is enabled.

## EOS

EOS is not one form followed by one calculation. Its public surface includes
persistent datasets, fitting attempts, parameter constraints, accepted and
rejected records, diagnostics and resuming a previous session.

Its GUI therefore needs a dedicated workspace with editable tables, model and
solver selectors, parameter and bounds editors, fit history and persistent
session state. Forcing all of this into the generic workflow form would make the
interface less clear and less faithful to the backend.

## Thermoelasticity

Thermoelasticity combines fitting choices, quality and stability policies,
uncertainty propagation and several P-T analysis or comparison modes. Some
fields have strict relationships; for example, a comparison may require exactly
one fixed coordinate between pressure and temperature.

The GUI should use thematic sections, numeric fields with clear units and
explicit cross-field validation. Final scientific validation still belongs to
Quantas.

## Implementation consequence

Workflow pages should not hand-build a wall of Dash components. Each workflow
defines a `FormSchema`, reuses the common field catalogue and gives a small
adapter responsibility for constructing the relevant public Quantas
dataclasses. Nested API objects become nested or collapsible form sections
rather than flattened, hard-to-read field names.
