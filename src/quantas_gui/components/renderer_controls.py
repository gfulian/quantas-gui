"""Reusable controls shared by table, Plotly, and message renderers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dash import dcc, html

from quantas_gui.components.controls import labelled_dropdown
from quantas_gui.explorer.models import (
    PlotFamilyDescriptor,
    ScientificExportDescriptor,
    TableFamilyDescriptor,
)
from quantas_gui.presentation.scientific_labels import scientific_label_text
from quantas_gui.renderers.plotly import COLORMAP_OPTIONS, PlotDescriptor

PLOT_APPEARANCE_DEFAULTS: dict[str, Any] = {
    "colormap": "source",
    "visibility": ["legend", "grid", "axes"],
    "hover": "closest",
    "line_width": "source",
    "line_color": "source",
    "axis_label_mode": "cartesian",
    "projection": "source",
    "contour_options": ["isolines"],
    "contour_levels": 0,
    "polarization": ["polarization"],
    "polarization_stride": 8,
    "polarization_width": "source",
    "polarization_scale": "source",
    "polarization_color": "source",
    "surface_opacity": 1.0,
    "camera": "source",
    "colorbar": ["colorbar"],
}

_LINE_COLOR_OPTIONS: tuple[tuple[str, str], ...] = (
    ("From result", "source"),
    ("Quantas blue", "#2994d1"),
    ("Sky blue", "#69bce8"),
    ("Orange", "#ed8a28"),
    ("Teal", "#50c6a9"),
    ("Red", "#f06c75"),
    ("Violet", "#b79cff"),
    ("Gold", "#f0b75a"),
    ("Black", "#111111"),
    ("White", "#f7fafc"),
)


def renderer_toolbar(controls: Sequence[Any], *, actions: Sequence[Any] = ()) -> html.Div:
    """Create the common responsive renderer toolbar."""
    return html.Div(
        [
            html.Div(list(controls), className="q-renderer-controls"),
            html.Div(list(actions), className="q-renderer-actions"),
        ],
        className="q-renderer-toolbar q-panel",
    )


def family_selector(*, component_id: str, label: str, families: Sequence[Any]) -> html.Label:
    """Create a selector for lazily generated scientific artifact families."""
    default = next(
        (item.key for item in families if item.default),
        families[0].key if families else None,
    )
    return labelled_dropdown(
        component_id=component_id,
        label=label,
        options=[item.as_option() for item in families],
        value=default,
        clearable=False,
        class_name="q-control--wide",
    )


def family_note(
    family: PlotFamilyDescriptor | TableFamilyDescriptor | None,
) -> html.Div:
    """Create a compact cost and scientific-description note."""
    if family is None:
        return html.Div()
    return html.Div(
        [
            html.Span(
                family.cost.upper(),
                className=f"q-cost-badge is-{family.cost}",
            ),
            html.Span(family.description),
        ],
        className="q-family-note",
    )


def table_selector(
    *,
    component_id: str,
    tables: Sequence[Any],
    value: str = "0",
    groups: Sequence[str] | None = None,
) -> html.Label:
    """Create the table selector for one prepared report family."""
    return labelled_dropdown(
        component_id=component_id,
        label="Table",
        options=[
            {
                "label": scientific_label_text(
                    f"{groups[index]} · {table.title}"
                    if groups and index < len(groups)
                    else str(table.title)
                ),
                "value": str(index),
            }
            for index, table in enumerate(tables)
        ],
        value=value,
        clearable=False,
        class_name="q-control--wide",
    )


def scientific_export_selector(
    *,
    component_id: str,
    exports: Sequence[ScientificExportDescriptor],
) -> html.Label:
    """Create a selector for public Quantas scientific export operations."""
    default = next((item.key for item in exports if item.enabled), None)
    return labelled_dropdown(
        component_id=component_id,
        label="Scientific export",
        options=[item.as_option() for item in exports],
        value=default,
        clearable=False,
        searchable=False,
        class_name="q-control--wide",
    )


def page_size_selector(*, component_id: str, value: int = 50) -> html.Label:
    """Create the table page-size selector."""
    return labelled_dropdown(
        component_id=component_id,
        label="Rows per page",
        options=[{"label": str(item), "value": item} for item in (20, 50, 100, 250)],
        value=value,
        clearable=False,
        searchable=False,
    )


def plot_selector(*, component_id: str, plots: Sequence[PlotDescriptor]) -> html.Label:
    """Create the selector for figures in one prepared plot family."""
    return labelled_dropdown(
        component_id=component_id,
        label="Figure",
        options=[item.as_option() for item in plots],
        value=plots[0].key if plots else None,
        clearable=False,
        class_name="q-control--wide",
    )


def colormap_selector(*, component_id: str, value: str = "source") -> html.Label:
    """Create a cosmetic colormap selector."""
    return labelled_dropdown(
        component_id=component_id,
        label="Colormap",
        options=[{"label": label, "value": name} for label, name in COLORMAP_OPTIONS],
        value=value,
        clearable=False,
    )


def hover_selector(*, component_id: str, value: str = "closest") -> html.Label:
    """Create the Plotly hover-mode selector."""
    return labelled_dropdown(
        component_id=component_id,
        label="Hover",
        options=[
            {"label": "Closest", "value": "closest"},
            {"label": "Unified X", "value": "x unified"},
            {"label": "Unified Y", "value": "y unified"},
        ],
        value=value,
        clearable=False,
        searchable=False,
    )


def line_width_selector(*, component_id: str) -> html.Label:
    """Create a renderer-only line-width override."""
    values = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)
    return labelled_dropdown(
        component_id=component_id,
        label="Line width",
        options=[{"label": "From result", "value": "source"}]
        + [{"label": f"{value:g} px", "value": value} for value in values],
        value="source",
        clearable=False,
        searchable=False,
    )


def line_color_selector(*, component_id: str, label: str = "Line colour") -> html.Label:
    """Create a portable line-colour override with a source-preserving default."""
    return labelled_dropdown(
        component_id=component_id,
        label=label,
        options=[{"label": title, "value": value} for title, value in _LINE_COLOR_OPTIONS],
        value="source",
        clearable=False,
        searchable=False,
    )


def axis_label_mode_selector(*, component_id: str) -> html.Label:
    """Create Cartesian or crystallographic directional-axis labels."""
    return labelled_dropdown(
        component_id=component_id,
        label="Directional axes",
        options=[
            {"label": "Cartesian (x, y, z)", "value": "cartesian"},
            {"label": "Crystallographic ([100], [010], [001])", "value": "crystal"},
        ],
        value="cartesian",
        clearable=False,
        searchable=False,
    )


def spherical_projection_selector(*, component_id: str, value: str = "source") -> html.Label:
    """Create the spherical-map projection selector."""
    return labelled_dropdown(
        component_id=component_id,
        label="Spherical projection",
        options=[
            {"label": "From result", "value": "source"},
            {"label": "Equal area", "value": "equal_area"},
            {"label": "Stereographic", "value": "stereographic"},
        ],
        value=value,
        clearable=False,
        searchable=False,
    )


def camera_selector(*, component_id: str) -> html.Label:
    """Create the 3D camera preset selector."""
    return labelled_dropdown(
        component_id=component_id,
        label="3D camera",
        options=[
            {"label": label, "value": value}
            for label, value in (
                ("Keep current", "source"),
                ("Isometric", "isometric"),
                ("Front", "front"),
                ("Top", "top"),
                ("Side", "side"),
            )
        ],
        value="source",
        clearable=False,
        searchable=False,
    )


def surface_opacity_control(*, component_id: str) -> html.Label:
    """Create a surface-opacity slider for 3D figures."""
    return html.Label(
        [
            html.Span("Surface opacity", className="q-control-label"),
            dcc.Slider(
                id=component_id,
                min=0.15,
                max=1.0,
                step=0.05,
                value=1.0,
                marks={
                    0.25: "25%",
                    0.5: "50%",
                    0.75: "75%",
                    1.0: "100%",
                },
                tooltip={"placement": "bottom", "always_visible": False},
                className="q-slider",
            ),
        ],
        className="q-control q-control--wide",
    )


def contour_level_control(*, component_id: str) -> html.Label:
    """Create an isoline-count control; zero preserves the public specification."""
    return html.Label(
        [
            html.Span("Number of isolines", className="q-control-label"),
            dcc.Slider(
                id=component_id,
                min=0,
                max=40,
                step=1,
                value=0,
                marks={0: "Source", 8: "8", 16: "16", 24: "24", 32: "32", 40: "40"},
                tooltip={"placement": "bottom", "always_visible": False},
                className="q-slider",
            ),
        ],
        className="q-control q-control--wide",
    )


def plot_visibility_toggles(
    *,
    component_id: str,
    value: Sequence[str] = ("legend", "grid", "axes"),
) -> dcc.Checklist:
    """Create shared legend, grid, and axis visibility controls."""
    return dcc.Checklist(
        id=component_id,
        options=[
            {"label": "Legend", "value": "legend"},
            {"label": "Grid", "value": "grid"},
            {"label": "Axes", "value": "axes"},
        ],
        value=list(value),
        inline=True,
        className="q-render-checklist",
    )


def contour_toggles(*, component_id: str) -> dcc.Checklist:
    """Create contour-line and contour-label controls."""
    return dcc.Checklist(
        id=component_id,
        options=[
            {"label": "Isolines", "value": "isolines"},
            {"label": "Line labels", "value": "labels"},
        ],
        value=["isolines"],
        inline=True,
        className="q-render-checklist",
    )


def colorbar_toggle(*, component_id: str) -> dcc.Checklist:
    """Create a colorbar visibility control."""
    return dcc.Checklist(
        id=component_id,
        options=[{"label": "Colorbar", "value": "colorbar"}],
        value=["colorbar"],
        inline=True,
        className="q-render-checklist",
    )


def polarization_toggle(*, component_id: str) -> dcc.Checklist:
    """Create a visibility switch for public polarization-axis layers."""
    return dcc.Checklist(
        id=component_id,
        options=[{"label": "Show polarizations", "value": "polarization"}],
        value=["polarization"],
        inline=True,
        className="q-render-checklist",
    )


def polarization_stride_selector(*, component_id: str) -> html.Label:
    """Create the visual sampling stride for dense polarization overlays."""
    return labelled_dropdown(
        component_id=component_id,
        label="Polarization stride",
        options=[
            {"label": f"Every {value}", "value": value} for value in (1, 2, 4, 6, 8, 10, 12, 16, 20)
        ],
        value=8,
        clearable=False,
        searchable=False,
    )


def polarization_line_width_selector(*, component_id: str) -> html.Label:
    """Create a display-only polarization line-width override."""
    values = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
    return labelled_dropdown(
        component_id=component_id,
        label="Polarization width",
        options=[{"label": "From result", "value": "source"}]
        + [{"label": f"{value:g} px", "value": value} for value in values],
        value="source",
        clearable=False,
        searchable=False,
    )


def polarization_scale_selector(*, component_id: str) -> html.Label:
    """Create a display-only polarization-axis length override."""
    values = (0.04, 0.05, 0.065, 0.08, 0.10, 0.12, 0.16)
    return labelled_dropdown(
        component_id=component_id,
        label="Polarization length",
        options=[{"label": "From result", "value": "source"}]
        + [{"label": f"{100.0 * value:g}%", "value": value} for value in values],
        value="source",
        clearable=False,
        searchable=False,
    )


def message_level_selector(*, component_id: str, levels: Sequence[str]) -> html.Label:
    """Create the multi-select event-level filter."""
    return labelled_dropdown(
        component_id=component_id,
        label="Levels",
        options=[{"label": level.upper(), "value": level} for level in levels],
        value=list(levels),
        clearable=False,
        multi=True,
        class_name="q-control--wide",
    )


def message_search_control(*, component_id: str) -> html.Label:
    """Create the stored-message text filter."""
    return html.Label(
        [
            html.Span("Search", className="q-control-label"),
            dcc.Input(
                id=component_id,
                type="search",
                placeholder="Filter messages…",
                debounce=True,
                className="q-input",
            ),
        ],
        className="q-control q-control--wide",
    )
