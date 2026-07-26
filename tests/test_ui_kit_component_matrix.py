"""Runtime construction matrix for every reusable scientific form field."""

from __future__ import annotations

from dataclasses import replace

import pytest

try:
    import dash
    import dash_ag_grid
    import plotly
    from dash import dash_table, dcc
    from dash._utils import to_json

    from quantas_gui.compat import (
        DASH_AG_GRID_BASELINE,
        DASH_AG_GRID_CALLBACK_PROPERTIES,
        DASH_AG_GRID_PROBE_ARGUMENTS,
        DASH_AG_GRID_USED_PROPERTIES,
        DASH_BASELINE,
        DASH_CORE_CALLBACK_PROPERTIES,
        DASH_CORE_PROBE_ARGUMENTS,
        DASH_CORE_USED_PROPERTIES,
        DASH_TABLE_PROBE_ARGUMENTS,
        DASH_TABLE_USED_PROPERTIES,
        PLOTLY_BASELINE,
        instantiate_component_probe,
    )
    from quantas_gui.forms.catalog import ui_kit_form
    from quantas_gui.forms.renderer import render_field, render_form
except ImportError as error:  # pragma: no cover - environment-dependent skip
    pytest.skip(str(error), allow_module_level=True)


def test_installed_frontend_versions_match_the_validated_baseline() -> None:
    assert dash.__version__ == DASH_BASELINE
    assert dash_ag_grid.__version__ == DASH_AG_GRID_BASELINE
    assert plotly.__version__ == PLOTLY_BASELINE


def test_installed_component_classes_expose_the_project_contract() -> None:
    contracts = (
        (
            dcc,
            DASH_CORE_USED_PROPERTIES,
            DASH_CORE_CALLBACK_PROPERTIES,
            DASH_CORE_PROBE_ARGUMENTS,
        ),
        (
            dash_table,
            DASH_TABLE_USED_PROPERTIES,
            {},
            DASH_TABLE_PROBE_ARGUMENTS,
        ),
        (
            dash_ag_grid,
            DASH_AG_GRID_USED_PROPERTIES,
            DASH_AG_GRID_CALLBACK_PROPERTIES,
            DASH_AG_GRID_PROBE_ARGUMENTS,
        ),
    )
    failures: list[str] = []
    for (
        module,
        constructor_contract,
        callback_contract,
        probe_arguments,
    ) in contracts:
        for component_name, used_properties in constructor_contract.items():
            component_type = getattr(module, component_name)
            component = instantiate_component_probe(
                component_type,
                probe_arguments.get(component_name, {}),
            )
            required = used_properties | callback_contract.get(
                component_name, frozenset()
            )
            missing = sorted(required - set(component.available_properties))
            if missing:
                failures.append(f"{module.__name__}.{component_name}: {missing}")
    assert not failures, "Installed component contract failures:\n" + "\n".join(failures)


def test_complete_ui_kit_form_constructs_and_serializes() -> None:
    assert to_json(render_form(ui_kit_form()))


@pytest.mark.parametrize("disabled", [False, True], ids=["enabled", "disabled"])
def test_every_ui_kit_field_constructs_and_serializes(disabled: bool) -> None:
    """Exercise every control family in both enabled and disabled states."""
    failures: list[str] = []
    schema = ui_kit_form()
    for field in schema.fields:
        candidate = replace(field, disabled=disabled)
        try:
            component = render_field("compatibility-matrix", candidate)
            assert to_json(component)
        except Exception as error:  # pragma: no cover - condensed diagnostic
            failures.append(f"{field.kind.value}:{field.key}: {error!r}")
    assert not failures, "UI component compatibility failures:\n" + "\n".join(failures)
