# Dash component compatibility baseline

Quantas GUI currently validates one exact frontend stack:

- Dash **4.4.1**;
- Dash AG Grid **35.2.0**;
- Plotly **6.9.0**.

The versions are pinned while the shared component system is in alpha. This
prevents a frontend release from changing a generated component signature
without being detected by CI. The runtime dependency remains independent from
Quantas itself.

## Disabled-state matrix

| Quantas GUI field | Dash implementation | Disabled strategy |
|---|---|---|
| short text | `dcc.Input` | component `disabled` |
| multiline text | `dcc.Textarea` | component `disabled` |
| integer / float | `dcc.Input` | component `disabled` |
| scientific number | text `dcc.Input` | component `disabled`; `inputMode="verbatim"` |
| radio selector | `dcc.RadioItems` | `disabled` on every option |
| checklist | `dcc.Checklist` | `disabled` on every option |
| boolean switch / checkbox | one-option `dcc.Checklist` | `disabled` on the option |
| select / multi-select | `dcc.Dropdown` | component `disabled`; option-level state remains supported |
| slider | `dcc.Slider` | component `disabled` |
| range slider | `dcc.RangeSlider` | component `disabled` |
| exact start-stop-step | three `dcc.Input` children | each child disabled |
| vector | repeated `dcc.Input` children | each child disabled |
| matrix | Dash AG Grid | numeric columns become non-editable |
| repeatable list | Dash AG Grid | value column becomes non-editable |
| key/value editor | Dash AG Grid + HTML buttons | columns non-editable and row actions disabled |
| file upload | `dcc.Upload` | component `disabled` |

`dcc.RadioItems` and `dcc.Checklist` do not expose a container-level
`disabled` keyword in Dash 4.4.1. Their options may be disabled individually.
This distinction is encoded in the renderer rather than hidden in a generic
keyword dictionary.

## Constructor audit

`tests/test_dash_441_contract.py` parses every call to `dcc`, `dash_table`, and
`dash_ag_grid` constructors in the package. It compares the properties used by
Quantas GUI with the explicit project contract in
`quantas_gui.compat.dash_441`.

The audit is deliberately limited to properties that Quantas GUI actually
uses. A small reviewed surface is easier to maintain than a copied version of
the complete upstream API.

## Runtime audit

Run the full installed-stack audit from the repository root:

```powershell
python tools/audit_dash_components.py
```

The command reports each field separately, in enabled and disabled states. It
also constructs and serializes the complete UI Kit, calls `/_dash-layout` and
`/_dash-dependencies`, and constructs every registered page. Any incompatible
component is reported by field kind and stable key rather than merely as an
HTTP 500 response.

For the ordinary repository checks:

```powershell
python tools/run_checks.py --skip-build
```

The runtime component audit is part of this command and of GitHub Actions.

## Upgrading Dash

A Dash, Dash AG Grid, or Plotly upgrade is an explicit maintenance task:

1. update `constraints/ui-baseline.txt`;
2. update the exact dependencies in `pyproject.toml`;
3. compare generated component signatures;
4. update `quantas_gui.compat`;
5. run the runtime matrix on Windows, Linux, and macOS;
6. inspect the UI Kit in a browser before merging.

No frontend version is broadened merely because a newer release exists.

## Metadata probes for required components

The runtime contract audit instantiates generated component classes to inspect
``available_properties``. Components whose React metadata marks a property as
required need harmless probe values even though no layout is being rendered.
The Dash 4.4.1 baseline currently defines:

- ``dcc.Link(href="/")``;
- ``dcc.Location(id="quantas-gui-compat-location")``.

These values belong only to compatibility inspection and are not application
defaults.
