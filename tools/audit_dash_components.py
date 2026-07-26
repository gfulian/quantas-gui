"""Audit every Quantas GUI component against the installed Dash runtime."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _require_version(installed: str, required: str) -> None:
    if installed != required:
        raise RuntimeError(f"installed {installed}; required {required}")


def _record(results: list[str], failures: list[str], label: str, action: Any) -> None:
    try:
        action()
    except Exception as error:  # noqa: BLE001 - audit reports all component failures
        failures.append(f"{label}: {type(error).__name__}: {error}")
        print(f"[FAIL] {label}\n       {type(error).__name__}: {error}")
    else:
        results.append(label)
        print(f"[PASS] {label}")


def main(argv: list[str] | None = None) -> int:
    """Construct and serialize the complete reusable UI surface."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=ROOT / ".audit-workspace")
    args = parser.parse_args(argv)

    try:
        import dash
        import dash_ag_grid
        import plotly
        from dash import dash_table, dcc
        from dash._utils import to_json
    except ImportError as error:
        print(f"[FAIL] frontend import: {error}")
        return 2

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

    print(f"Dash: {dash.__version__} (required {DASH_BASELINE})")
    print(
        f"Dash AG Grid: {dash_ag_grid.__version__} "
        f"(required {DASH_AG_GRID_BASELINE})"
    )
    print(f"Plotly: {plotly.__version__} (required {PLOTLY_BASELINE})")

    from quantas_gui.app import create_app
    from quantas_gui.config import Settings
    from quantas_gui.forms.catalog import ui_kit_form
    from quantas_gui.forms.renderer import render_field

    passed: list[str] = []
    failures: list[str] = []

    for label, installed, required in (
        ("Dash version", dash.__version__, DASH_BASELINE),
        ("Dash AG Grid version", dash_ag_grid.__version__, DASH_AG_GRID_BASELINE),
        ("Plotly version", plotly.__version__, PLOTLY_BASELINE),
    ):
        _record(
            passed,
            failures,
            label,
            lambda installed=installed, required=required: _require_version(
                installed, required
            ),
        )

    component_contracts = (
        (
            "dcc",
            dcc,
            DASH_CORE_USED_PROPERTIES,
            DASH_CORE_CALLBACK_PROPERTIES,
            DASH_CORE_PROBE_ARGUMENTS,
        ),
        (
            "dash_table",
            dash_table,
            DASH_TABLE_USED_PROPERTIES,
            {},
            DASH_TABLE_PROBE_ARGUMENTS,
        ),
        (
            "dash_ag_grid",
            dash_ag_grid,
            DASH_AG_GRID_USED_PROPERTIES,
            DASH_AG_GRID_CALLBACK_PROPERTIES,
            DASH_AG_GRID_PROBE_ARGUMENTS,
        ),
    )
    for (
        namespace,
        module,
        constructor_contract,
        callback_contract,
        probe_arguments,
    ) in component_contracts:
        for component_name, used_properties in constructor_contract.items():
            callback_properties = callback_contract.get(component_name, frozenset())
            required_properties = used_properties | callback_properties

            def inspect_component(
                module=module,
                component_name=component_name,
                required_properties=required_properties,
                probe_arguments=probe_arguments,
            ) -> None:
                component_type = getattr(module, component_name)
                component = instantiate_component_probe(
                    component_type,
                    probe_arguments.get(component_name, {}),
                )
                available = set(component.available_properties)
                missing = sorted(required_properties - available)
                if missing:
                    raise RuntimeError("missing properties: " + ", ".join(missing))

            _record(
                passed,
                failures,
                f"component {namespace}.{component_name} property contract",
                inspect_component,
            )

    schema = ui_kit_form()
    for field in schema.fields:
        for disabled in (False, True):
            state = "disabled" if disabled else "enabled"
            label = f"field {field.kind.value}/{field.key} ({state})"

            def construct(field=field, disabled=disabled) -> None:
                component = render_field(
                    "runtime-audit",
                    replace(field, disabled=disabled),
                )
                if not to_json(component):
                    raise RuntimeError("empty serialized component")

            _record(passed, failures, label, construct)

    settings = Settings.local_defaults().with_overrides(
        workspace_root=args.workspace,
        open_browser=False,
    )
    app = create_app(settings)

    def shell_endpoint() -> None:
        response = app.server.test_client().get("/_dash-layout")
        if response.status_code != 200:
            raise RuntimeError(f"/_dash-layout returned {response.status_code}")

    _record(passed, failures, "application /_dash-layout", shell_endpoint)

    def dependencies_endpoint() -> None:
        response = app.server.test_client().get("/_dash-dependencies")
        if response.status_code != 200:
            raise RuntimeError(f"/_dash-dependencies returned {response.status_code}")

    _record(
        passed,
        failures,
        "application /_dash-dependencies",
        dependencies_endpoint,
    )

    for page in dash.page_registry.values():
        path = str(page.get("path", page.get("module", "unknown")))

        def construct_page(page=page) -> None:
            factory = page.get("layout")
            component = factory() if callable(factory) else factory
            if not to_json(component):
                raise RuntimeError("empty serialized page")

        _record(passed, failures, f"page {path}", construct_page)

    print(f"\nSummary: {len(passed)} passed, {len(failures)} failed")
    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
