"""Shared helpers for structural rendering of Quantas plot specifications."""

from __future__ import annotations

from math import ceil
from typing import Any

import numpy as np
import plotly.graph_objects as go

from quantas_gui.renderers.plotly.options import PlotlyRenderOptions

_BRAND_COLORS = (
    "#69bce8",
    "#ed8a28",
    "#50c6a9",
    "#f06c75",
    "#b79cff",
    "#f0b75a",
    "#8ad4f5",
    "#d6e7f2",
)


def axis_title(axis: Any) -> str:
    """Return a readable label with optional units."""
    label = str(getattr(axis, "label", getattr(axis, "key", "Value")))
    unit = getattr(axis, "unit", None)
    return f"{label} [{unit}]" if unit else label


def colorscale(name: str | None) -> str:
    """Map portable Quantas names to Plotly colorscale identifiers."""
    if not name:
        return "Viridis"
    normalized = str(name).strip().lower().replace("-", "").replace("_", "")
    aliases = {
        "viridis": "Viridis",
        "cividis": "Cividis",
        "plasma": "Plasma",
        "inferno": "Inferno",
        "magma": "Magma",
        "turbo": "Turbo",
        "rdbu": "RdBu",
        "rdylbu": "RdYlBu",
        "spectral": "Spectral",
        "coolwarm": "RdBu",
        "seismic": "RdBu",
        "rainbow": "Turbo",
        "jet": "Turbo",
    }
    return aliases.get(normalized, str(name))


def line_dash(value: str | None) -> str:
    """Map portable line styles to Plotly dash names."""
    return {
        "solid": "solid",
        "dashed": "dash",
        "dash": "dash",
        "dotted": "dot",
        "dot": "dot",
        "dashdot": "dashdot",
        "-": "solid",
        "--": "dash",
        ":": "dot",
        "-.": "dashdot",
    }.get(str(value), "solid")


def marker_symbol(value: str | None) -> str:
    """Map common Matplotlib-like markers to Plotly symbols."""
    return {
        None: "circle",
        "o": "circle",
        "circle": "circle",
        "s": "square",
        "square": "square",
        "^": "triangle-up",
        "v": "triangle-down",
        "<": "triangle-left",
        ">": "triangle-right",
        "d": "diamond",
        "diamond": "diamond",
        "x": "x",
        "+": "cross",
        "*": "star",
    }.get(value, "circle")


def series_color(index: int, requested: str | None) -> str:
    """Resolve a portable requested color or a branded deterministic fallback."""
    return requested or _BRAND_COLORS[index % len(_BRAND_COLORS)]


def apply_layout(
    figure: go.Figure,
    *,
    title: str,
    options: PlotlyRenderOptions,
    three_dimensional: bool = False,
) -> go.Figure:
    """Apply the Quantas visual theme and interaction defaults."""
    dark = options.template == "quantas_dark"
    paper = "#0d2030" if dark else "#ffffff"
    plot = "#071522" if dark else "#ffffff"
    text = "#ecf5fb" if dark else "#10283a"
    grid = "rgba(174, 211, 232, 0.11)" if dark else "rgba(16, 40, 58, 0.12)"
    axis = "rgba(174, 211, 232, 0.24)" if dark else "rgba(16, 40, 58, 0.25)"
    figure.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        paper_bgcolor=paper,
        plot_bgcolor=plot,
        font={"color": text, "family": "Inter, system-ui, sans-serif", "size": 12},
        margin={"l": 66, "r": 35, "t": 72, "b": 62},
        hovermode=options.hover_mode,
        hoverlabel={"bgcolor": "#10283a", "font": {"color": "#ecf5fb"}},
        legend={
            "bgcolor": "rgba(4, 16, 26, 0.72)" if dark else "rgba(255,255,255,0.85)",
            "bordercolor": axis,
            "borderwidth": 1,
        },
        showlegend=options.show_legend,
        modebar={"bgcolor": "rgba(4, 16, 26, 0.7)", "color": text},
        uirevision=options.uirevision,
    )
    if three_dimensional:
        figure.update_layout(
            scene={
                "bgcolor": plot,
                "xaxis": _scene_axis(options, grid, axis),
                "yaxis": _scene_axis(options, grid, axis),
                "zaxis": _scene_axis(options, grid, axis),
                "aspectmode": "data",
                **_camera(options.camera),
            }
        )
    else:
        figure.update_xaxes(
            showgrid=options.show_grid,
            gridcolor=grid,
            linecolor=axis,
            zerolinecolor=grid,
            visible=options.show_axes,
        )
        figure.update_yaxes(
            showgrid=options.show_grid,
            gridcolor=grid,
            linecolor=axis,
            zerolinecolor=grid,
            visible=options.show_axes,
        )
    return figure


def subplot_grid(count: int, columns: int) -> tuple[int, int]:
    """Return a positive row/column grid for a panel collection."""
    resolved_columns = max(1, min(int(columns), max(1, count)))
    return max(1, ceil(count / resolved_columns)), resolved_columns


def array(value: Any) -> np.ndarray:
    """Return a NumPy array without copying when possible."""
    return np.asarray(value)


def limits(value: Any) -> tuple[float | None, float | None]:
    """Normalize optional axis or color limits."""
    if value is None:
        return None, None
    lower, upper = value
    return (
        None if lower is None else float(lower),
        None if upper is None else float(upper),
    )


def _scene_axis(options: PlotlyRenderOptions, grid: str, axis: str) -> dict[str, Any]:
    return {
        "showgrid": options.show_grid,
        "gridcolor": grid,
        "linecolor": axis,
        "zerolinecolor": grid,
        "visible": options.show_axes,
        "showbackground": False,
    }


def _camera(value: str) -> dict[str, Any]:
    """Return an optional stable Plotly camera preset."""
    presets: dict[str, dict[str, Any]] = {
        "isometric": {"camera": {"eye": {"x": 1.45, "y": 1.45, "z": 1.25}}},
        "front": {"camera": {"eye": {"x": 0.0, "y": 2.2, "z": 0.0}}},
        "top": {"camera": {"eye": {"x": 0.0, "y": 0.0, "z": 2.2}}},
        "side": {"camera": {"eye": {"x": 2.2, "y": 0.0, "z": 0.0}}},
    }
    return presets.get(str(value), {})
