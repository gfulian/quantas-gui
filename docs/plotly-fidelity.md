# Plotly scientific fidelity

The Result Explorer turns public Quantas plot specifications into interactive
Plotly figures. That translation may improve navigation, responsiveness and
presentation, but it must not create a new scientific interpretation of the
result.

## What defines the figure

Validation follows this order:

1. the public Quantas plot specification and its documented fields;
2. the arrays, labels, units, limits, masks and metadata stored in that
   specification;
3. the current Quantas Matplotlib rendering of the same specification, used as
   a development reference for visual meaning;
4. the Quantas GUI Plotly renderer.

The GUI never imports the Matplotlib renderer at runtime. Side-by-side
comparison is a validation method, not an application dependency.

## What must remain equivalent

For the same specification, the two frontends must agree on:

- the physical quantity and dimensionality being shown;
- Cartesian, polar, spherical or three-dimensional geometry;
- projection and hemisphere conventions;
- the meaning of lines, markers, contours, surfaces, masks, uncertainties and
  overlays;
- source colours and line styles when they are explicitly part of the
  specification;
- labels, mathematical symbols, units, limits and colour normalization;
- extrema, tensor-frame directions and polarization directions.

Plotly may add hover text, zoom, camera movement, responsive layout, trace
visibility and export controls. Those features may not modify the source values
or the scientific specification.

## Labels, units and colour values

Mathematical labels are converted into Plotly-compatible text without changing
the symbol or unit. Numeric arrays remain in the units supplied by Quantas.
Display precision is a renderer choice; stored precision and exported raw data
remain untouched.

Frontend-neutral style values can occasionally use a colour notation understood
by Matplotlib but not by CSS. The Plotly renderer normalizes only the colour
syntax. It does not reinterpret the data or choose a different scientific
scale.

## Thermoelastic profiles and P-T coverage

Profile plots must preserve the original pressure, temperature or depth axis,
the selected elastic component and every mask or uncertainty band supplied by
Quantas. P-T maps must retain source grid orientation, domain limits, contour
levels and normalization.

A visual slice at fixed pressure or temperature is not the same as a new
scientific interpolation. The GUI can request an existing public slice or hide
traces, but any numerical transformation must be performed by Quantas.

## Theme and export

Dark and light themes may adapt background, grid, text and otherwise invisible
black or white strokes. Theme adaptation must not change the scientific colour
mapping, level boundaries or trace identity.

PNG and browser exports should reproduce the visible figure with readable text
and a clear background. CSV and native scientific exports come from the source
contracts rather than reverse-engineering values from Plotly traces.

## Polar plots

Principal-plane polar plots must preserve the plane, angular convention,
component and radial values. Closing a curve, rotating the visual start angle or
changing tick placement is acceptable only when it matches the meaning declared
by the specification.

## Spherical maps

Spherical maps require particular care with longitude, latitude, hemisphere and
projection. Masks and extrema must remain attached to the correct positions.
Changing projection is a presentation choice; rotating a tensor or physical
reference frame is a scientific operation and must use a public Quantas
transformation.

Polarization vectors are normalized only for drawing. Their displayed length,
line width and colour are presentation options, while direction and branch
identity remain those supplied by Quantas.

## Three-dimensional directional surfaces

A 3D surface must preserve its radial property, angular sampling, colour field,
mask and any source vectors. Camera position, opacity and lighting are visual
controls. They must not alter the coordinates or recalculate the surface.

Extrema and frame vectors should remain visible and scientifically labelled.
When a source colour would disappear against the active theme, the renderer may
choose a readable visual equivalent and must keep that adaptation limited to
presentation.

## How a plot family is signed off

A synthetic PlotSpec proving that the renderer does not crash is not enough.
Each module needs representative native HDF5 results and a recorded comparison
covering:

- source plot family and key;
- Matplotlib and Plotly outputs compared from the same specification;
- dimensions, units, limits and normalization;
- correspondence of lines, contours, surfaces and overlays;
- dark, light and system themes;
- desktop and narrow viewports;
- PNG export and transparent-background behaviour;
- performance and cache reuse;
- accepted differences and their scientific impact.

Any difference that can change scientific interpretation blocks sign-off for
the Result Explorer milestone.
