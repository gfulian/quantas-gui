# SEISMIC workflow

The SEISMIC page turns an elastic tensor and a density into directional acoustic
properties. It follows the same application pattern as Elasticity: prepare the
input, choose the scientific options, start a background job, review the
summary, and open the native result in the Result Explorer.

This page explains the workflow as a user experiences it. Scientific formulas,
units, tolerances and result construction remain in Quantas and are reached
through the public `quantas.api.seismic` contract.

## Preparing the input

The workflow needs three things:

- a job name;
- a 6 × 6 elastic stiffness tensor in GPa;
- a finite positive density in kg m⁻³.

There are four supported ways to provide them.

### Manual input

Paste the stiffness matrix and enter the density directly. The matrix field
accepts:

- a complete 6 × 6 matrix;
- a compact upper triangle with row lengths `6, 5, 4, 3, 2, 1`;
- a compact lower triangle with row lengths `1, 2, 3, 4, 5, 6`;
- a 6 × 6 triangular matrix whose unused half is filled with zeros.

Compact triangular input is expanded into a symmetric matrix before the public
request is built. A complete matrix with values in both triangles is not
silently averaged or corrected; Quantas performs the final scientific
validation.

### Quantas input

A shared Quantas Elasticity/SEISMIC input can populate the job name, stiffness
and density. Elasticity ignores the density field, while SEISMIC requires it.

### CRYSTAL and VASP output

CRYSTAL outputs and VASP `OUTCAR` files are handled through
`quantas.api.seismic.create_input()`. The uploaded file remains in the
controlled workspace, and the extracted values populate the editable form.
Always review the imported tensor and density before submitting the job.

## Choosing the calculation

### Angular grid

`ntheta` and `nphi` control the directional sampling. A denser grid produces
smoother maps and surfaces but takes longer and creates a larger result. The GUI
keeps the execution batch size as an internal detail so progress remains useful
without changing the scientific grid.

### Hemisphere

- **Upper** samples the upper hemisphere.
- **Lower** samples the lower hemisphere.
- **Full** samples the complete sphere.

Choose the smallest domain that answers the scientific question. Full-sphere
sampling is useful when inversion-related directions must be inspected
explicitly.

### Calculation level

- **Phase** calculates phase velocities and mode information.
- **Group** adds group velocities and power-flow quantities.
- **Enhancement** adds the most expensive enhancement diagnostics.

Each level includes the preceding one. Choosing enhancement therefore requests
phase, group and enhancement fields in the native result.

### Polarization continuity

Polarization-axis tracking keeps mode orientations continuous across the sampled
grid where the public backend can do so. It is useful for polarization overlays
and interpretation near mode changes. Degenerate directions can still require
careful scientific reading.

### Advanced numerical settings

The advanced section exposes public tolerances for eigenvalues, degeneracy,
pseudoinverse handling and caustic candidates. The defaults come from Quantas
and should normally be kept unless the user has a specific numerical reason to
change them.

### Physical tensor rotation

A physical rotation changes the tensor or reference basis before the calculation.
It is not the same as rotating the Plotly camera. The workflow supports the
public XYZ-angle and 3 × 3 transformation contracts.

## Running the job

The calculation runs in a separate local process rather than inside a Dash HTTP
callback. The page reports:

- queued, running, cancelling, succeeded, failed or cancelled state;
- the current phase of work;
- monotonic progress and current/total counters when available;
- ordered information, warning and error messages;
- cooperative cancellation at the next safe checkpoint.

Closing or refreshing the browser does not stop the server-side job. Restarting
the application process is different: persistent restart recovery is not yet a
claimed feature of the local alpha backend.

A non-positive-definite stiffness matrix cannot produce a valid SEISMIC result.
That case ends as a failed job and no HDF5 result is published. Invalid or
missing density is rejected as well.

## Completion summary and downloads

A successful job shows a compact report-based summary, including the density,
sampling choices, elastic averages, isotropic reference velocities and the
available directional diagnostics.

The page offers:

- **Download HDF5** for the authoritative native Quantas result;
- **Download report** for the deterministic text report;
- **Download sampled CSV** for the supported public sampled-field export;
- **Open in Result Explorer** for detailed tables and interactive figures.

The workflow page deliberately does not duplicate the complete Result Explorer.

## Understanding the 3D views

SEISMIC provides two complementary surface families.

### General scalar-field surface

Use this family for sampled scalar properties such as:

- shear-wave anisotropy;
- shear splitting;
- P-to-S velocity ratios;
- power-flow angle;
- enhancement.

Several scalar properties can be selected in one build. After Compute, switch
between the cached figures without rebuilding the scientific collection.
Depending on the property, the surface shape and the colour can represent
different quantities.

### Acoustic wave surface

Use this family for the canonical physical surfaces of the selected acoustic
mode:

- phase velocity;
- slowness;
- group wavefront;
- P, S1 or S2 mode.

Several surface types and modes can be built together and switched afterward.
This is usually the clearest view when the question concerns the acoustic
surface itself rather than a derived scalar diagnostic.

## Validation status

The `0.4.0a4` closing baseline has been checked against the public Quantas API.
Stiffness and density are preserved exactly. Elastic averages and isotropic
reference velocities agree within `rtol=1e-14`, `atol=1e-14`; phase, group and
enhancement fields agree within `rtol=1e-12`, `atol=1e-12`.

Real-data workflow checks include a VASP OHAp output and a CRYSTAL calcite
output. Native HDF5 reopening, sampled CSV export, progress, controlled failure,
result handoff and multi-property surface caching are covered.
