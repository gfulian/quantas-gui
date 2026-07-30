# Audit of Quantas CLI controls

## Why this audit exists

The CLI is the most complete inventory of operations and options already
available to Quantas users. The GUI does not call it at runtime; it is inspected
only during development so that new forms do not overlook established
capabilities.

The original inventory was prepared against `2.0.0b6`, while the current GUI
baseline is `2.0.0b7`. Every item must therefore be checked against the current
`quantas.api` contract and tests before implementation.

## What the inventory tells us

Many CLI options repeat across `run`, `plot` and `export` commands and across
scientific modules. Translating each occurrence into a separate widget would
produce a large and inconsistent interface. Most options fit a much smaller set
of reusable control families:

| CLI family | GUI interpretation |
|---|---|
| boolean flag | switch or explicit acknowledgement |
| discrete choice | radio, dropdown, checklist or multi-select |
| integer or floating-point value | exact numeric input |
| input path | controlled upload or workspace reference |
| output path | download name or result identifier |
| repeated values | editable list or multi-select |
| vector or interval | labelled composite control |
| matrix | validated numeric grid |

The recurring CLI sections — units, calculation domain, scientific model,
numerical method, diagnostics, plotting and output — can become shared form
sections.

## Important mappings

- `START STOP STEP` domains become three exact inputs, not sliders.
- An `X Y Z` rotation becomes a labelled vector.
- Isotherms, isobars, components and profiles become lists or multi-selectors,
  depending on whether values are free or drawn from known choices.
- EOS parameters, starting values and bounds become an editable table.
- A 6×6 elastic tensor uses a numeric matrix with copy, paste and symmetry
  validation.
- Destructive actions such as overwrite or `force` require explicit
  acknowledgement.
- Extrapolation, failure and stability policies should include a brief
  explanation of their consequences.

## Final rule

The CLI audit protects completeness, but it does not define the GUI runtime.
The final form must follow the scientific meaning and public Quantas dataclasses.
Options that exist only for the terminal or the Matplotlib frontend should not
be copied automatically into Dash.
