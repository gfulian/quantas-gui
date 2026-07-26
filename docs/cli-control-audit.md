# Quantas CLI control audit

## Scope

The audit was performed against Quantas `2.0.0b6`. It found 47 command/group
nodes, including 37 operational leaf commands. Counting repeated common options,
the Click surface exposes 573 value-bearing parameters and 253 distinct
parameter names.

This number is not the number of GUI widgets to implement. Repetition across
`run`, `plot`, `export`, and module families collapses into a compact reusable
control catalogue.

## Raw parameter families

| Click family | Repeated occurrences | GUI interpretation |
|---|---:|---|
| boolean flags | 131 | switch or acknowledgement checkbox |
| choices | 121 | radio, select, checklist, or multi-select |
| bounded floats | 89 | precise number input; slider only when appropriate |
| file paths | 85 | upload, result reference, workspace target, or download |
| free text | 58 | text, multiline text, tags, or key/value records |
| bounded integers | 47 | integer input, occasionally paired with a slider |
| unbounded floats | 38 | float/scientific-number input |
| multi-value options | 22 | checklist, multi-select, or repeatable list |
| fixed arity greater than one | 13 | vector or start/stop/step composite |

## Recurrent semantic groups

The CLI already groups options by meaning. The most common headings are:

- Output and reporting;
- Lines and markers;
- Figure geometry and typography;
- Scientific model;
- Plotting;
- Validation and diagnostics;
- Calculation domain;
- Style;
- Units;
- Axes and annotations;
- Component selection;
- Numerical method.

These headings should become reusable `FormSection` patterns, not a flat wall
of controls.

## Important mappings

- `--temperature START STOP STEP`, pressure and depth ranges become exact
  range-triplet controls, not range sliders.
- `--rotate-xyz X Y Z` becomes a labeled three-vector.
- repeated isotherms, isobars, pressures, temperatures, components, and profile
  names become repeatable lists or multi-selectors according to whether the
  values are open or drawn from known choices.
- EOS fixed parameters, initial parameters, and bounds become editable
  parameter records rather than repeated strings.
- 6×6 elastic tensors use a numeric matrix grid with symmetry validation and
  copy/paste support.
- `--force` and overwrite operations require an explicit acknowledgement
  checkbox and a confirmation policy; they are not ordinary switches.
- verbosity, extrapolation, failure, stability, and validation policies should
  use labeled selectors with concise explanations of their consequences.
- paths that represent browser inputs are uploads. Paths that represent outputs
  become filenames, downloads, or opaque workspace references.

## Source of truth

The CLI audit is necessary for completeness, but GUI forms must be checked
against the public API dataclasses and functions before implementation. Some
CLI options are presentation-only, some combine several API objects, and some
paths have different meaning in a browser/server application.
