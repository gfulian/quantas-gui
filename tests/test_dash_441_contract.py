"""Static contract audit for the Dash 4.4.1 component surface."""

from __future__ import annotations

import ast
from pathlib import Path

from quantas_gui.compat.dash_441 import (
    DASH_AG_GRID_USED_PROPERTIES,
    DASH_CORE_PROBE_ARGUMENTS,
    DASH_CORE_USED_PROPERTIES,
)

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "quantas_gui"


def _literal_dict_keys(node: ast.AST) -> set[str]:
    if not isinstance(node, ast.Dict):
        return set()
    return {
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def _mapping_keys(scope: ast.AST) -> dict[str, set[str]]:
    mappings: dict[str, set[str]] = {}
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign):
            keys = _literal_dict_keys(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name) and keys:
                    mappings.setdefault(target.id, set()).update(keys)
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "update":
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        name = node.func.value.id
        keys = {keyword.arg for keyword in node.keywords if keyword.arg is not None}
        for argument in node.args:
            keys.update(_literal_dict_keys(argument))
        if keys:
            mappings.setdefault(name, set()).update(keys)
    return mappings


def _component_contract(namespace: str, component: str) -> frozenset[str] | None:
    if namespace == "dcc":
        return DASH_CORE_USED_PROPERTIES.get(component)
    if namespace == "dag":
        return DASH_AG_GRID_USED_PROPERTIES.get(component)
    return None


def test_component_keywords_match_the_dash_441_project_contract() -> None:
    """Reject unsupported component props before a page is opened in Dash."""
    violations: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        scopes: list[ast.AST] = [
            node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for scope in scopes:
            mappings = _mapping_keys(scope)
            for node in ast.walk(scope):
                if not isinstance(node, ast.Call):
                    continue
                function = node.func
                if not isinstance(function, ast.Attribute):
                    continue
                if not isinstance(function.value, ast.Name):
                    continue
                namespace = function.value.id
                contract = _component_contract(namespace, function.attr)
                if contract is None:
                    continue
                used = {keyword.arg for keyword in node.keywords if keyword.arg is not None}
                for keyword in node.keywords:
                    if keyword.arg is None and isinstance(keyword.value, ast.Name):
                        used.update(mappings.get(keyword.value.id, set()))
                unsupported = sorted(prop for prop in used if prop not in contract)
                if unsupported:
                    relative = path.relative_to(SOURCE_ROOT.parent)
                    violations.append(
                        f"{relative}:{node.lineno}: {namespace}.{function.attr}: "
                        + ", ".join(unsupported)
                    )
    assert not violations, "Unsupported Dash 4.4.1 properties:\n" + "\n".join(violations)


def test_radio_and_checklist_disable_through_options_not_container_props() -> None:
    """Dash 4.4.1 has no component-level disabled prop for these controls."""
    path = SOURCE_ROOT / "forms" / "renderer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if not (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "dcc"
            and function.attr in {"RadioItems", "Checklist"}
        ):
            continue
        checked += 1
        explicit = {keyword.arg for keyword in node.keywords if keyword.arg is not None}
        assert "disabled" not in explicit, (
            f"dcc.{function.attr} at line {node.lineno} uses unsupported disabled="
        )
    assert checked >= 3
    source = path.read_text(encoding="utf-8")
    assert "force_disabled=field.disabled" in source
    assert '"disabled": field.disabled' in source


def test_required_component_probe_arguments_are_explicit() -> None:
    """Keep required Dash constructor values in the pinned compatibility layer."""
    assert DASH_CORE_PROBE_ARGUMENTS["Link"] == {"href": "/"}
    assert DASH_CORE_PROBE_ARGUMENTS["Location"] == {"id": "quantas-gui-compat-location"}
    assert DASH_CORE_PROBE_ARGUMENTS["Store"] == {"id": "quantas-gui-compat-store"}


def test_component_probe_discovers_generated_required_arguments() -> None:
    """Do not maintain a brittle exception list for generated required props."""
    from quantas_gui.compat.dash_441 import instantiate_component_probe

    class GeneratedLikeComponent:
        def __init__(self, **arguments: object) -> None:
            if "id" not in arguments:
                raise TypeError("Required argument `id` was not specified.")
            if "href" not in arguments:
                raise TypeError("Required argument `href` was not specified.")
            self.arguments = arguments
            self.available_properties = ["id", "href"]

    component = instantiate_component_probe(GeneratedLikeComponent)

    assert component.arguments["id"] == "quantas-gui-component-probe"
    assert component.arguments["href"] == "/"
