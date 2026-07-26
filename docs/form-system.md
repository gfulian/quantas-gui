# Declarative scientific form system

## Purpose

Quantas GUI uses a reusable form system rather than writing independent Dash
controls directly inside every workflow page. The same principle that is useful
in a PyQt application applies to Dash, but the implementation must account for
Dash's callback and browser/server state model.

The form system separates four concerns:

1. **schema** — what one scientific option means;
2. **renderer** — which Dash component presents it;
3. **validation and coercion** — how browser values become typed Python values;
4. **workflow adapter** — how validated values construct public `quantas.api`
   input and option dataclasses.

The GUI schema is not a replacement for the Quantas API. Quantas dataclass
constructors and workflow functions remain the final scientific validation
boundary.

## Runtime dependency rule

The CLI is useful as a complete migration inventory, but the GUI runtime must
not import `quantas.cli`, Click commands, or Click parameter types.

```text
Quantas CLI metadata ── development audit only
                              │
                              ▼
GUI form schemas ──► Dash renderer ──► public quantas.api dataclasses
```

`tools/audit_quantas_cli.py` can be run against an installed Quantas checkout to
compare the current command surface with the GUI control catalogue. It is not
imported by the application.

## Stable field families

The initial schema supports:

- text and multiline text;
- integer and floating-point values, including scientific notation;
- switches and acknowledgement checkboxes;
- select, radio, checklist, and multi-select choices;
- scalar and range sliders;
- exact start/stop/step ranges;
- fixed-length vectors;
- editable numeric matrices;
- browser file uploads;
- repeatable scalar lists;
- editable key/value records;
- declarative visibility and enablement conditions;
- cross-field rules such as exactly-one and mutual exclusion.

## Control-selection policy

The renderer does not map every number to a slider.

| Scientific intent | Preferred control |
|---|---|
| tolerance, convergence threshold, exact P or T | numeric input |
| `start, stop, step` calculation domain | range-triplet composite |
| bounded visual opacity or confidence | slider |
| two to four common exclusive choices | radio group |
| longer exclusive list | dropdown |
| short multiple-choice list | checklist |
| long multiple-choice list | multi-select |
| arbitrary repeated values | editable one-column list |
| stiffness tensor or other rectangular data | matrix grid |
| parameter constraints or initial guesses | key/value grid |
| destructive `force` or overwrite action | acknowledgement checkbox |
| ordinary feature flag | switch |
| input path in a browser | controlled upload, never a server path string |
| output path in a browser | download name or workspace result reference |

## Dash-specific design

Most Dash form components expose their value through a `value` property.
Composite controls and grids do not. The form layer therefore exposes helpers
that generate the correct callback `State` dependency for each field and
normalize component-specific data before validation.

Range triplets and vectors aggregate their sub-inputs into lightweight
`dcc.Store` components. Matrices and key/value controls use Dash AG Grid
`rowData`. Upload fields remain page-service responsibilities because uploaded
bytes must be moved promptly into a controlled workspace rather than retained
as global process state.

Dash pattern-matching callbacks are used only for reusable component mechanics.
Workflow callbacks should use generated static dependencies from an immutable
`FormSchema`; this keeps callback graphs inspectable and avoids one enormous
callback handling every page.

## Server readiness

The form schema contains no Flask session, filesystem path, worker object, or
large numerical result. A server deployment can therefore reuse the same
schemas and renderers while replacing only upload, job, and result services.
Browser persistence is opt-in per field and should be limited to harmless user
preferences. Scientific input files, matrices from files, and results remain in
server-side workspaces.

## Package layout

```text
quantas_gui/forms/
├── schema.py       passive form contracts
├── ids.py          aligned pattern-matching identifiers
├── values.py       component-value adapters
├── validation.py   pure field and cross-field validation
├── bindings.py     generated Dash State dependencies
├── callbacks.py    reusable composite-control mechanics
├── renderer.py     Dash and AG Grid renderer
└── catalog.py      representative reusable schemas
```

Runtime feedback components live separately in
`quantas_gui.components.feedback` because logs, warnings, progress, and results
are outputs rather than form fields.
