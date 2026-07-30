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
    responsive_css = (SOURCE_ROOT / "assets" / "30_responsive.css").read_text(encoding="utf-8")
    shell_source = (SOURCE_ROOT / "components" / "shell.py").read_text(encoding="utf-8")

    assert "flex-direction: column" in layout_css
    assert "overflow-y: auto" in layout_css
    assert ".q-sidebar-footer" in layout_css and "position: static" in layout_css
    assert "UI_KIT_NAV" in shell_source
    assert "items = UI_KIT_NAV" in shell_source
    assert "overflow-x: auto" in responsive_css
    assert "Settings" in shell_source
    assert "UI Kit" in shell_source


def test_every_registered_page_layout_constructs_and_serializes(tmp_path: Path) -> None:
    """Exercise lazy page factories in both packaged application profiles."""
    dash = pytest.importorskip("dash")
    pytest.importorskip("dash_ag_grid")
    from dash._utils import to_json

    from quantas_gui.app import create_app
    from quantas_gui.config import Settings
    from quantas_gui.profile import ApplicationProfile

    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    failures: list[str] = []
    for profile in (ApplicationProfile.STANDARD, ApplicationProfile.UI_KIT):
        create_app(settings, profile=profile)
        for page in tuple(dash.page_registry.values()):
            layout_factory = page.get("layout")
            try:
                layout = layout_factory() if callable(layout_factory) else layout_factory
                payload = to_json(layout)
                assert payload
            except Exception as error:  # pragma: no cover - reported as one useful failure
                failures.append(
                    f"{profile.value}:{page.get('path', page.get('module'))}: {error!r}"
                )

    assert not failures, "Page layout failures:\n" + "\n".join(failures)


def test_plotly_graph_enables_mathjax_and_slider_values_are_theme_readable() -> None:
    result_source = (SOURCE_ROOT / "components" / "result_renderers.py").read_text(encoding="utf-8")
    form_css = (SOURCE_ROOT / "assets" / "50_forms.css").read_text(encoding="utf-8")
    assert "mathjax=True" in result_source
    assert ".rc-slider-tooltip-inner" in form_css
    assert "color: var(--q-text);" in form_css
    assert ".rc-slider-mark-text-active" in form_css


def test_system_theme_is_default_and_is_rechecked_client_side() -> None:
    preference_source = (SOURCE_ROOT / "models" / "preferences.py").read_text(encoding="utf-8")
    callback_source = (SOURCE_ROOT / "callbacks" / "settings.py").read_text(encoding="utf-8")
    shell_source = (SOURCE_ROOT / "components" / "shell.py").read_text(encoding="utf-8")
    bootstrap_source = (SOURCE_ROOT / "assets" / "05_theme_bootstrap.js").read_text(
        encoding="utf-8"
    )
    assert 'theme: str = "system"' in preference_source
    assert 'theme: "system"' in callback_source
    assert "prefers-color-scheme: light" in callback_source
    assert "q-system-theme-watch" in callback_source
    assert "q-system-theme-watch" in shell_source
    assert "prefers-color-scheme: light" in bootstrap_source
    assert 'media.addEventListener("change", applySystemTheme)' in bootstrap_source


def test_result_plot_controls_are_collapsible_and_grouped_by_plot_kind() -> None:
    result_source = (SOURCE_ROOT / "components" / "result_renderers.py").read_text(encoding="utf-8")
    callback_source = (SOURCE_ROOT / "callbacks" / "result_plots.py").read_text(encoding="utf-8")
    result_css = (SOURCE_ROOT / "assets" / "40_results.css").read_text(encoding="utf-8")

    assert "def plot_control_drawer() -> html.Details" in result_source
    assert 'html.Span("Figure controls")' in result_source
    for section in (
        "Interaction",
        "Visibility",
        "Lines",
        "Colour and scale",
        "Contours",
        "Directional axes",
        "Spherical projection",
        "Polarization overlays",
        "Three-dimensional view",
    ):
        assert f'"{section}"' in result_source
    assert "plot_control_configuration" in callback_source
    for component_id in (
        "PLOT_LINE_WIDTH",
        "PLOT_LINE_COLOR",
        "PLOT_AXIS_LABEL_MODE",
        "PLOT_CONTOUR_LEVELS",
        "PLOT_POLARIZATION_STRIDE",
        "PLOT_POLARIZATION_SCALE",
        "PLOT_POLARIZATION_WIDTH",
        "PLOT_POLARIZATION_COLOR",
    ):
        assert component_id in result_source
        assert component_id in callback_source
    assert ".q-plot-control-drawer[open]" in result_css
    assert ".q-plot-workbench" in result_css
    assert ".q-plot-polarization-controls" in result_css


def test_table_export_distinguishes_view_csv_from_scientific_exports() -> None:
    result_source = (SOURCE_ROOT / "components" / "result_renderers.py").read_text(encoding="utf-8")
    table_source = (SOURCE_ROOT / "renderers" / "tables.py").read_text(encoding="utf-8")

    assert "Download full table (CSV)" in result_source
    assert "Scientific exports" in result_source
    assert "Grid filters and sorting are visual only" in result_source
    assert "table_grid_payload" in table_source
    assert '"agNumberColumnFilter"' in table_source


def test_result_grid_and_dash4_theme_tokens_do_not_collide() -> None:
    table_source = (SOURCE_ROOT / "renderers" / "tables.py").read_text(encoding="utf-8")
    component_css = (SOURCE_ROOT / "assets" / "20_components.css").read_text(encoding="utf-8")
    result_css = (SOURCE_ROOT / "assets" / "40_results.css").read_text(encoding="utf-8")
    token_css = (SOURCE_ROOT / "assets" / "00_tokens.css").read_text(encoding="utf-8")
    form_css = (SOURCE_ROOT / "assets" / "50_forms.css").read_text(encoding="utf-8")

    assert 'className="ag-theme-quartz-dark q-report-grid"' in table_source
    assert ".q-report-grid" in result_css
    assert ".q-results-grid" in component_css
    assert "--Dash-Text-Primary" in token_css
    assert "--Dash-Fill-Inverse-Strong" in token_css
    assert '[role="combobox"]' in form_css
    assert ".q-render-checklist label" in form_css


def test_native_plot_description_uses_unicode_scientific_labels() -> None:
    callback_source = (SOURCE_ROOT / "callbacks" / "result_plots.py").read_text(encoding="utf-8")
    assert 'scientific_label_text(descriptor.get("title"' in callback_source
    assert 'scientific_label_text(descriptor.get("description"' in callback_source


def test_ag_grid_legacy_theme_assets_are_loaded_by_the_application_factory() -> None:
    app_source = (SOURCE_ROOT / "app.py").read_text(encoding="utf-8")
    table_source = (SOURCE_ROOT / "renderers" / "tables.py").read_text(encoding="utf-8")

    assert "import dash_ag_grid as dag" in app_source
    assert "external_stylesheets=[dag.themes.BASE, dag.themes.QUARTZ]" in app_source
    callback_source = (SOURCE_ROOT / "callbacks" / "result_tabs.py").read_text(encoding="utf-8")
    result_source = (SOURCE_ROOT / "components" / "result_renderers.py").read_text(encoding="utf-8")

    assert '"theme": "legacy"' in table_source
    assert 'className="ag-theme-quartz-dark q-report-grid"' in table_source
    assert "initial_tables: Sequence[Any] = ()" in result_source
    assert "service.build_tables(reference, selected_table_family.key)" in callback_source


def test_scientific_build_controls_are_separate_from_plotly_display_controls() -> None:
    result_source = (SOURCE_ROOT / "components" / "result_renderers.py").read_text(encoding="utf-8")
    callback_source = (SOURCE_ROOT / "callbacks" / "result_plots.py").read_text(encoding="utf-8")
    service_source = (SOURCE_ROOT / "services" / "results.py").read_text(encoding="utf-8")

    assert "def scientific_selection_panel" in result_source
    assert (
        "from quantas_gui.presentation.scientific_labels import scientific_label_text"
        in result_source
    )
    assert "Build selected view" in result_source
    assert "def plot_control_drawer" in result_source
    assert "configure_scientific_selection" in callback_source
    assert "build_scientific_plot_family" in callback_source
    assert "PLOT_SCIENCE_SELECTION" in callback_source
    assert "selection.cache_token()" in service_source


def test_result_callbacks_are_decomposed_by_responsibility() -> None:
    facade = (SOURCE_ROOT / "callbacks" / "results.py").read_text(encoding="utf-8")
    for module in (
        "result_session",
        "result_tabs",
        "result_tables",
        "result_plots",
        "result_messages",
        "result_downloads",
    ):
        assert module in facade
    assert len(facade.splitlines()) < 60


def test_result_orchestration_delegates_module_presentation_to_backend() -> None:
    service_source = (SOURCE_ROOT / "services" / "results.py").read_text(encoding="utf-8")
    backend_source = (SOURCE_ROOT / "services" / "result_backend.py").read_text(encoding="utf-8")

    assert "quantas_gui.explorer.adapters" not in service_source
    assert "self.backend.table_group" in service_source
    assert "self.backend.plot_group" in service_source
    assert "self.backend.plot_description" in service_source
    assert "from quantas_gui.explorer.adapters import adapter_for" in backend_source


def test_active_result_store_and_plot_state_controls_are_global_and_explicit() -> None:
    shell_source = (SOURCE_ROOT / "components" / "shell.py").read_text(encoding="utf-8")
    result_shell = (SOURCE_ROOT / "components" / "result_shell.py").read_text(encoding="utf-8")
    renderer_source = (SOURCE_ROOT / "components" / "result_renderers.py").read_text(
        encoding="utf-8"
    )
    plot_callbacks = (SOURCE_ROOT / "callbacks" / "result_plots.py").read_text(encoding="utf-8")

    assert "dcc.Store(id=ResultIds.SESSION" in shell_source
    assert "dcc.Store(id=ResultIds.SESSION" not in result_shell
    assert "Selection changed — rebuild required" in plot_callbacks
    assert "Reset selection" in renderer_source
    assert "Reset figure appearance" in renderer_source
    assert "PLOT_ACTIVE_SUMMARY" in renderer_source
