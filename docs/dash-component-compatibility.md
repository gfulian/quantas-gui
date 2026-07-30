# Dash component compatibility

During the alpha phase, Quantas GUI validates one exact frontend stack:

- Dash `4.4.1`;
- Dash AG Grid `35.2.0`;
- Plotly `6.9.0`.

The pins are not intended to avoid upgrades. They make upgrades deliberate and
repeatable. A new frontend release can change component properties,
serialization or generated markup, so it must be tested before entering the
main branch.

## Themes and disabled states

Shared controls must work in both Quantas Dark and Quantas Light. Library CSS
variables are mapped to the Quantas design tokens, while small fallback rules
cover components whose generated DOM may change.

Disabled behaviour is not uniform across Dash. For example,
`dcc.RadioItems` and `dcc.Checklist` disable individual options, while a
`dcc.Input` disables the component itself. The form renderer handles these
details so scientific pages do not have to.

| GUI field | Implementation | Disabled behaviour |
|---|---|---|
| text and numbers | `dcc.Input` / `dcc.Textarea` | component property |
| radio and checklist | `dcc.RadioItems` / `dcc.Checklist` | disabled options |
| dropdown | `dcc.Dropdown` | component property |
| slider | `dcc.Slider` / `dcc.RangeSlider` | component property |
| vectors and ranges | several `dcc.Input` children | every child disabled |
| matrices and lists | Dash AG Grid | columns become read-only |
| upload | `dcc.Upload` | component property |

## Automated checks

`tests/test_dash_441_contract.py` inspects the Dash and AG Grid properties used
by the source and compares them with the explicit contract in
`quantas_gui.compat.dash_441`.

Run the installed-stack audit from the repository root:

```powershell
python tools\audit_dash_components.py
```

The audit builds controls in enabled and disabled states, serializes both the
standard application and the UI Kit, requests `/_dash-layout` and
`/_dash-dependencies`, and constructs every registered page. A failure is
reported against a stable field key instead of appearing only as a generic HTTP
error.

The normal repository gate runs the same audit:

```powershell
python tools\run_checks.py
```

## Updating the baseline

A Dash, Dash AG Grid or Plotly upgrade should:

1. update `constraints/ui-baseline.txt` and `pyproject.toml`;
2. compare the generated component properties;
3. update `quantas_gui.compat` where necessary;
4. run the test matrix on Windows, Linux and macOS;
5. open `quantas-gui --ui-kit` and inspect both themes before merging.

Version ranges are not broadened simply because a newer release exists.

## Components that need probe values

Some generated component classes require a property even during metadata
inspection. The audit supplies harmless probe values, such as
`dcc.Link(href="/")` and a dedicated `dcc.Location` identifier. These values
belong only to the compatibility check and are not application defaults.
