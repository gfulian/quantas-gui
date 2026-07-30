# Module result adapters

Adapters give each scientific module room to organise its public reports, plots
and exports without turning the shared Explorer into a collection of special
cases.

An adapter may:

- group public report and plot families;
- choose clear interface labels and descriptions;
- expose selection fields from the public inventory;
- validate that a selected combination is listed by Quantas;
- describe valid scientific exports and downstream actions;
- provide read-only structural handling for EOS archives.

An adapter may not:

- import private Quantas modules;
- inspect HDF5 directly to discover scientific capability;
- reproduce a formula or calculation;
- invent properties or contexts missing from the public inventory;
- alter values to make a renderer easier to implement.

## Current modules

- **Elasticity** — report tables and directional property plots.
- **SEISMIC** — velocity, anisotropy, projection, polarization and 3D families.
- **HA** — temperature and optional volume-dependent thermodynamic views.
- **QHA** — pressure, temperature, volume, slice and map contexts.
- **Thermoelasticity** — fit diagnostics, P–T fields, profiles and component
  layouts.
- **EOS** — read-only archive datasets, records, parameters, quality and
  diagnostic plots.

## Placement rule

If behaviour has the same meaning for several modules, put it in a shared
component, service or renderer. If it decides which scientific choice is valid
for one module, keep it in that module's adapter or workflow package.

## Selection contract

Adapters translate inventory entries into `PlotBuildSelection` values. These
values are lightweight, serializable and stable enough to form a cache
fingerprint. Presentation settings are deliberately excluded.
