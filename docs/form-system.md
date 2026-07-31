# Declarative scientific form system

## Why it exists

Quantas workflows have different scientific options, but many controls carry
the same meaning: numbers with units, domains, matrices, method choices,
failure policies and uploads. Building every page by hand would quickly create
inconsistent controls and difficult callback code.

Quantas GUI therefore separates four responsibilities:

1. the **schema** describes what a field means;
2. the **renderer** chooses the appropriate Dash component;
3. **GUI validation** converts browser values into structurally valid Python
   data;
4. the **workflow adapter** constructs public `quantas.api` objects.

Final scientific validation always remains in Quantas.

## Relationship with the CLI

The CLI is useful for inventory and terminology, but it is not imported by the
GUI runtime.

```text
Quantas CLI ── development audit only
                         │
                         ▼
FormSchema → Dash renderer → public quantas.api dataclasses
```

`tools/audit_quantas_cli.py` helps compare the two frontends without creating a
Click dependency.

## Field families

The shared catalogue includes:

- text and multiline text;
- integers, floats and scientific notation;
- switches and explicit acknowledgements;
- radio groups, checklists, dropdowns and multi-selects;
- sliders only for values suited to visual adjustment;
- exact `start / stop / step` domains;
- fixed-length vectors;
- numeric matrices;
- controlled uploads;
- repeatable lists and key/value records;
- visibility and enablement conditions;
- cross-field rules such as mutual exclusion or “exactly one”.

## Choosing the right control

| Meaning | Preferred control |
|---|---|
| tolerance or exact P/T value | numeric input |
| `start / stop / step` domain | three-value composite |
| opacity or visual adjustment | slider |
| a few exclusive choices | radio group |
| a long exclusive list | dropdown |
| several known choices | checklist or multi-select |
| arbitrary repeated values | editable list |
| tensor or rectangular data | numeric grid |
| parameters, guesses and bounds | key/value grid |
| destructive operation | explicit acknowledgement |
| input file | controlled upload |
| output file | download name or result reference |

## Dash integration

Simple controls normally expose a `value`; matrices, lists and composite
controls do not. The form layer therefore generates the correct `State`
dependencies and normalizes `rowData`, vectors and domains before validation.

Uploads are handed to a controlled workspace immediately. They are not kept in
global variables or left in browser storage as large payloads.

Pattern-matching callbacks are reserved for reusable component mechanics. Each
workflow uses static dependencies generated from its schema, keeping the
callback graph understandable.

## Server compatibility

A schema contains no Flask session, filesystem path, worker or numerical result.
The same pages can therefore use local or server backends by replacing upload,
execution and persistence services rather than rewriting the forms.

## Package layout

```text
quantas_gui/forms/
├── schema.py       passive contracts
├── ids.py          stable identifiers
├── values.py       Dash value adapters
├── validation.py   pure validation
├── bindings.py     generated State dependencies
├── callbacks.py    composite-control mechanics
├── renderer.py     Dash and AG Grid renderer
└── catalog.py      reusable schemas
```

Progress, logs, warnings and errors live in
`quantas_gui.components.feedback` because they are workflow outputs, not form
fields.

## UI Kit

The UI Kit is a developer test surface. It is absent from normal navigation and
starts explicitly with:

```text
quantas-gui --ui-kit
```

It uses the same renderers, assets, themes and callbacks as the main
application, so problems found there are meaningful for real workflows.
## Elasticity reference implementation

`0.3.0a2` is the first executable use of the form system. Its schema keeps the
scientific choices separate from Dash callbacks:

- job name and a multiline 6 × 6 stiffness matrix in GPa;
- direct paste or controlled import from Quantas, CRYSTAL and VASP sources;
- public 2D/3D sampling choices and selected 3D properties;
- optional physical tensor rotation in an advanced section;
- no density, manual symmetry, CLI rendering option or false unit selector.

The workflow callback normalizes widget values, constructs an
`ElasticityRequest`, and lets the process-side adapter build public
`quantas.api.elasticity` dataclasses. Selecting a file source requires a
matching successful import. Switching to manual paste clears unused source
provenance rather than attributing edited values to the wrong file.

The browser never retains the uploaded file after import. It receives only the
controlled workspace identifier, safe display metadata and editable scalar
form values.
