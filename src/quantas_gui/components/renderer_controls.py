"""Reusable controls shared by table, Plotly, and message renderers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dash import dcc, html

from quantas_gui.components.controls import labelled_dropdown
from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor
from quantas_gui.renderers.plotly import COLORMAP_OPTIONS, PlotDescriptor


def renderer_toolbar(controls: Sequence[Any], *, actions: Sequence[Any] = ()) -> html.Div:
    """Create the common responsive renderer toolbar."""
    return html.Div([
        html.Div(list(controls), className="q-renderer-controls"),
        html.Div(list(actions), className="q-renderer-actions"),
    ], className="q-renderer-toolbar q-panel")


def family_selector(*, component_id: str, label: str, families: Sequence[Any]) -> html.Label:
    """Create a selector for lazily generated scientific artifact families."""
    default = next((item.key for item in families if item.default), families[0].key if families else None)
    return labelled_dropdown(
        component_id=component_id, label=label,
        options=[item.as_option() for item in families], value=default,
        clearable=False, class_name="q-control--wide",
    )


def family_note(family: PlotFamilyDescriptor | TableFamilyDescriptor | None) -> html.Div:
    """Create a compact cost and scientific-description note."""
    if family is None:
        return html.Div()
    return html.Div([
        html.Span(family.cost.upper(), className=f"q-cost-badge is-{family.cost}"),
        html.Span(family.description),
    ], className="q-family-note")


def table_selector(*, component_id: str, tables: Sequence[Any], value: str = "0", groups: Sequence[str] | None = None) -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="Table",
        options=[
            {
                "label": (f"{groups[index]} · {table.title}" if groups and index < len(groups) else str(table.title)),
                "value": str(index),
            }
            for index, table in enumerate(tables)
        ],
        value=value, clearable=False, class_name="q-control--wide",
    )


def page_size_selector(*, component_id: str, value: int = 50) -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="Rows per page",
        options=[{"label": str(item), "value": item} for item in (20, 50, 100, 250)],
        value=value, clearable=False, searchable=False,
    )


def plot_selector(*, component_id: str, plots: Sequence[PlotDescriptor]) -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="Figure",
        options=[item.as_option() for item in plots], value=plots[0].key if plots else None,
        clearable=False, class_name="q-control--wide",
    )


def colormap_selector(*, component_id: str, value: str = "source") -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="Colormap",
        options=[{"label": label, "value": name} for label, name in COLORMAP_OPTIONS],
        value=value, clearable=False,
    )


def hover_selector(*, component_id: str, value: str = "closest") -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="Hover",
        options=[{"label": "Closest", "value": "closest"},
                 {"label": "Unified X", "value": "x unified"},
                 {"label": "Unified Y", "value": "y unified"}],
        value=value, clearable=False, searchable=False,
    )


def spherical_projection_selector(*, component_id: str, value: str = "source") -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="Spherical projection",
        options=[{"label": "From result", "value": "source"},
                 {"label": "Equal area", "value": "equal_area"},
                 {"label": "Stereographic", "value": "stereographic"}],
        value=value, clearable=False, searchable=False,
    )


def camera_selector(*, component_id: str) -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="3D camera",
        options=[{"label": label, "value": value} for label, value in (
            ("Keep current", "source"), ("Isometric", "isometric"),
            ("Front", "front"), ("Top", "top"), ("Side", "side"))],
        value="source", clearable=False, searchable=False,
    )


def surface_opacity_control(*, component_id: str) -> html.Label:
    return html.Label([
        html.Span("Surface opacity", className="q-control-label"),
        dcc.Slider(id=component_id, min=0.15, max=1.0, step=0.05, value=1.0,
                   marks={0.25: "25%", 0.5: "50%", 0.75: "75%", 1.0: "100%"},
                   tooltip={"placement": "bottom", "always_visible": False}),
    ], className="q-control q-control--wide")


def plot_visibility_toggles(*, component_id: str, value: Sequence[str] = ("legend", "grid", "axes")) -> dcc.Checklist:
    return dcc.Checklist(
        id=component_id,
        options=[{"label": "Legend", "value": "legend"}, {"label": "Grid", "value": "grid"},
                 {"label": "Axes", "value": "axes"}],
        value=list(value), inline=True, className="q-render-checklist",
    )


def contour_toggles(*, component_id: str) -> dcc.Checklist:
    return dcc.Checklist(
        id=component_id,
        options=[{"label": "Isolines", "value": "isolines"},
                 {"label": "Line labels", "value": "labels"}],
        value=["isolines"], inline=True, className="q-render-checklist",
    )


def colorbar_toggle(*, component_id: str) -> dcc.Checklist:
    return dcc.Checklist(
        id=component_id, options=[{"label": "Colorbar", "value": "colorbar"}],
        value=["colorbar"], inline=True, className="q-render-checklist",
    )


def message_level_selector(*, component_id: str, levels: Sequence[str]) -> html.Label:
    return labelled_dropdown(
        component_id=component_id, label="Levels",
        options=[{"label": level.upper(), "value": level} for level in levels],
        value=list(levels), clearable=False, multi=True, class_name="q-control--wide",
    )


def message_search_control(*, component_id: str) -> html.Label:
    return html.Label([
        html.Span("Search", className="q-control-label"),
        dcc.Input(id=component_id, type="search", placeholder="Filter messages…",
                  debounce=True, className="q-input"),
    ], className="q-control q-control--wide")
