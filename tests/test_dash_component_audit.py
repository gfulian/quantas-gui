"""Static and runtime guards for reusable Dash component factories."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "quantas_gui"


def _literal_mapping_keys(node: ast.AST) -> set[str]:
    if not isinstance(node, ast.Dict):
        return set()
    keys: set[str] = set()
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            keys.add(key.value)
    return keys


def _scope_duplicate_expansions(scope: ast.AST, path: Path) -> list[str]:
    mappings: dict[str, set[str]] = {}
    violations: list[str] = []

    class ScopeVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node is scope:
                self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node is scope:
                self.generic_visit(node)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            if node is scope:
                self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            keys = _literal_mapping_keys(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name) and keys:
                    mappings[target.id] = keys
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            explicit = {keyword.arg for keyword in node.keywords if keyword.arg is not None}
            for keyword in node.keywords:
                if keyword.arg is not None:
                    continue
                expanded: set[str] = set()
                if isinstance(keyword.value, ast.Name):
                    expanded = mappings.get(keyword.value.id, set())
                elif isinstance(keyword.value, ast.Dict):
                    expanded = _literal_mapping_keys(keyword.value)
                overlap = sorted(explicit & expanded)
                if overlap:
                    relative = path.relative_to(SOURCE_ROOT.parent)
                    violations.append(
                        f"{relative}:{node.lineno}: duplicate through **mapping: "
                        + ", ".join(overlap)
                    )
            self.generic_visit(node)

    ScopeVisitor().visit(scope)
    return violations


def test_literal_expanded_props_do_not_duplicate_explicit_keywords() -> None:
    """Catch failures such as ``Component(**common, className=...)`` early."""
    violations: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                violations.extend(_scope_duplicate_expansions(node, path))

    assert not violations, "\n".join(violations)


def test_dash_input_modes_stay_within_supported_public_values() -> None:
    """Keep generated dcc.Input controls compatible with Dash 4.x."""
    allowed = {
        None,
        "verbatim",
        "latin",
        "latin-name",
        "latin-prose",
        "full-width-latin",
        "kana",
        "katakana",
        "numeric",
        "tel",
        "email",
        "url",
    }
    violations: list[str] = []

    def literal_values(node: ast.AST) -> set[object]:
        if isinstance(node, ast.Constant):
            return {node.value}
        if isinstance(node, ast.IfExp):
            return literal_values(node.body) | literal_values(node.orelse)
        return set()

    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword) or node.arg != "inputMode":
                continue
            for value in literal_values(node.value):
                if value not in allowed:
                    relative = path.relative_to(SOURCE_ROOT.parent)
                    violations.append(f"{relative}:{node.lineno}: {value!r}")
    assert not violations, "Unsupported dcc.Input inputMode values:\n" + "\n".join(violations)


def test_sidebar_layout_is_scrollable_and_mobile_system_pages_are_reachable() -> None:
    layout_css = (SOURCE_ROOT / "assets" / "10_layout.css").read_text(encoding="utf-8")
    responsive_css = (SOURCE_ROOT / "assets" / "30_responsive.css").read_text(
        encoding="utf-8"
    )
    shell_source = (SOURCE_ROOT / "components" / "shell.py").read_text(encoding="utf-8")

    assert "flex-direction: column" in layout_css
    assert "overflow-y: auto" in layout_css
    assert ".q-sidebar-footer" in layout_css and "position: static" in layout_css
    assert "MOBILE_NAV = (*WORKSPACE_NAV, *SYSTEM_NAV)" in shell_source
    assert "overflow-x: auto" in responsive_css
    assert "Settings" in shell_source
    assert "UI Kit" in shell_source


def test_every_registered_page_layout_constructs_and_serializes(tmp_path: Path) -> None:
    """Exercise lazy page factories, including the Scientific UI Kit."""
    dash = pytest.importorskip("dash")
    pytest.importorskip("dash_ag_grid")
    from dash._utils import to_json

    from quantas_gui.app import create_app
    from quantas_gui.config import Settings

    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    create_app(settings)

    failures: list[str] = []
    for page in dash.page_registry.values():
        layout_factory = page.get("layout")
        try:
            layout = layout_factory() if callable(layout_factory) else layout_factory
            payload = to_json(layout)
            assert payload
        except Exception as error:  # pragma: no cover - reported as one useful failure
            failures.append(f"{page.get('path', page.get('module'))}: {error!r}")

    assert not failures, "Page layout failures:\n" + "\n".join(failures)
