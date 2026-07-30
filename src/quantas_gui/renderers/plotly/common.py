"""Shared helpers for structural rendering of Quantas plot specifications."""

from __future__ import annotations

import re
from math import ceil
from typing import Any

import numpy as np
import plotly.graph_objects as go

from quantas_gui.presentation.scientific_labels import (
    quantity_unit_label,
    scientific_math_label,
)
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
    """Return the complete public Quantas axis label without duplicating units.

    Quantas plot specifications document ``PlotAxis.label`` as the complete
    human-readable label. Some third-party or test specifications provide a
    shorter label and keep the unit only in ``PlotAxis.unit``; those receive a
    conservative ``"Label (unit)"`` fallback.
    """
    label = str(getattr(axis, "label", getattr(axis, "key", "Value"))).strip()
    unit = getattr(axis, "unit", None)
    return quantity_unit_label(label, unit)


def colorbar_options(
    axis: Any,
    *,
    compact: bool = False,
    horizontal: bool = False,
    x: float | None = None,
    y: float | None = None,
) -> dict[str, Any]:
    """Return a close, readable colorbar with a complete scientific label.

    Projected spherical maps follow the horizontal Matplotlib convention.
    Cartesian contours and 3D surfaces retain a vertical bar with its title
    parallel to the bar and close to the plotting domain.
    """
    if horizontal:
        return {
            "orientation": "h",
            "title": {
                "text": axis_title(axis),
                "side": "top",
                "font": {"size": 10 if compact else 12},
            },
            "tickfont": {"size": 9 if compact else 10},
            "thickness": 12 if compact else 14,
            "len": 0.58 if compact else 0.68,
            "x": 0.5 if x is None else x,
            "xanchor": "center",
            "y": -0.12 if y is None else y,
            "yanchor": "top",
            "ypad": 2,
            "outlinewidth": 0,
        }
    return {
        "orientation": "v",
        "title": {
            "text": axis_title(axis),
            "side": "right",
            "font": {"size": 11 if compact else 13},
        },
        "tickfont": {"size": 9 if compact else 11},
        "thickness": 14 if compact else 17,
        "len": 0.74 if compact else 0.80,
        "x": 0.995 if x is None else x,
        "xanchor": "left",
        "xpad": 3,
        "y": 0.5 if y is None else y,
        "yanchor": "middle",
        "outlinewidth": 0,
    }


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
        "quantaspowerflow": "Turbo",
        "quantasenhancement": "RdBu",
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


_SERIES_MARKER_CYCLE: tuple[str, ...] = (
    "circle",
    "square",
    "triangle-up",
    "triangle-down",
    "diamond-wide",
    "diamond",
    "cross",
    "x",
    "star",
    "pentagon",
    "hexagon",
    "hourglass",
)

_MATPLOTLIB_MARKERS: dict[str, str] = {
    "o": "circle",
    "circle": "circle",
    "s": "square",
    "square": "square",
    "^": "triangle-up",
    "v": "triangle-down",
    "<": "triangle-left",
    ">": "triangle-right",
    "D": "diamond-wide",
    "d": "diamond",
    "diamond": "diamond",
    "x": "x",
    "+": "cross",
    "*": "star",
    "p": "pentagon",
    "h": "hexagon",
    "H": "hexagon2",
    "8": "octagon",
}
_PLOTLY_MARKER_SYMBOLS = frozenset((*_SERIES_MARKER_CYCLE, *_MATPLOTLIB_MARKERS.values()))


def marker_symbol(value: str | None) -> str:
    """Map common Matplotlib-like markers to Plotly symbols."""
    if value is None:
        return "circle"
    return _MATPLOTLIB_MARKERS.get(value, value if value in _PLOTLY_MARKER_SYMBOLS else "circle")


def distinct_series_marker(index: int, requested: str | None, used: set[str]) -> str:
    """Return one stable marker that remains distinct within an overlay.

    Quantas already advertises Matplotlib-like markers for most multi-series
    thermoelastic profiles. The Plotly renderer preserves those markers when
    possible, translates variants such as ``D`` and ``d`` distinctly, and
    assigns a deterministic unused fallback when a source marker is absent or
    duplicated. This changes only presentation; the prepared series remain
    untouched.
    """
    if requested is not None:
        preferred = marker_symbol(requested)
        if preferred not in used:
            used.add(preferred)
            return preferred

    for offset in range(len(_SERIES_MARKER_CYCLE)):
        candidate = _SERIES_MARKER_CYCLE[(index + offset) % len(_SERIES_MARKER_CYCLE)]
        if candidate not in used:
            used.add(candidate)
            return candidate

    fallback = _SERIES_MARKER_CYCLE[index % len(_SERIES_MARKER_CYCLE)]
    used.add(fallback)
    return fallback


_MATPLOTLIB_SHORT_COLORS = {
    "b": "#0000ff",
    "g": "#008000",
    "r": "#ff0000",
    "c": "#00bfbf",
    "m": "#bf00bf",
    "y": "#bfbf00",
    "k": "#000000",
    "w": "#ffffff",
}
_MATPLOTLIB_CYCLE_PATTERN = re.compile(r"^[Cc](?P<index>\d+)$")


def portable_color(value: object | None, fallback: str) -> str:
    """Translate portable Matplotlib-like colours to Plotly CSS colours.

    Quantas plot specifications are frontend-neutral and may legitimately use
    Matplotlib grayscale strings such as ``"0.35"``. Plotly does not accept
    that notation, so the GUI translates it without changing the scientific
    data or the backend style contract.
    """
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback

    normalized = text.lower()
    if normalized == "none":
        return "rgba(0,0,0,0)"
    if normalized in _MATPLOTLIB_SHORT_COLORS:
        return _MATPLOTLIB_SHORT_COLORS[normalized]

    cycle = _MATPLOTLIB_CYCLE_PATTERN.fullmatch(text)
    if cycle is not None:
        index = int(cycle.group("index"))
        return _BRAND_COLORS[index % len(_BRAND_COLORS)]

    try:
        grayscale = float(text)
    except ValueError:
        return text
    if 0.0 <= grayscale <= 1.0:
        channel = round(255.0 * grayscale)
        return f"#{channel:02x}{channel:02x}{channel:02x}"
    return text


def series_color(index: int, requested: object | None) -> str:
    """Resolve a portable requested colour or a branded deterministic fallback."""
    fallback = _BRAND_COLORS[index % len(_BRAND_COLORS)]
    return portable_color(requested, fallback)


def theme_palette(options: PlotlyRenderOptions) -> dict[str, str]:
    """Return theme-dependent Plotly colors while keeping backgrounds transparent."""
    dark = options.template == "quantas_dark"
    return {
        "text": "#ecf5fb" if dark else "#142b3a",
        "text_soft": "#b3c7d5" if dark else "#365365",
        "grid": "rgba(174, 211, 232, 0.18)" if dark else "rgba(35, 74, 99, 0.16)",
        "axis": "rgba(214, 231, 242, 0.58)" if dark else "rgba(35, 74, 99, 0.58)",
        "zero": "rgba(237, 138, 40, 0.52)" if dark else "rgba(201, 108, 22, 0.48)",
        "legend": "rgba(4, 16, 26, 0.82)" if dark else "rgba(255, 255, 255, 0.90)",
        "hover": "#10283a" if dark else "#ffffff",
        "hover_text": "#ecf5fb" if dark else "#142b3a",
        "transparent": "rgba(0, 0, 0, 0)",
    }


def apply_layout(
    figure: go.Figure,
    *,
    title: str,
    options: PlotlyRenderOptions,
    three_dimensional: bool = False,
) -> go.Figure:
    """Apply the Quantas visual theme and interaction defaults."""
    palette = theme_palette(options)
    figure.update_layout(
        title={
            "text": scientific_math_label(title),
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 18},
        },
        paper_bgcolor=palette["transparent"],
        plot_bgcolor=palette["transparent"],
        font={"color": palette["text"], "family": "Inter, system-ui, sans-serif", "size": 13},
        margin={"l": 82, "r": 72, "t": 76, "b": 74},
        hovermode=options.hover_mode,
        hoverlabel={
            "bgcolor": palette["hover"],
            "bordercolor": palette["axis"],
            "font": {"color": palette["hover_text"], "size": 12},
        },
        legend={
            "bgcolor": palette["legend"],
            "bordercolor": palette["axis"],
            "borderwidth": 1,
            "font": {"size": 11},
        },
        showlegend=options.show_legend,
        modebar={"bgcolor": palette["transparent"], "color": palette["text"]},
        uirevision=options.uirevision,
        autosize=True,
    )
    if three_dimensional:
        figure.update_layout(
            scene={
                "bgcolor": palette["transparent"],
                "xaxis": _scene_axis(options, palette),
                "yaxis": _scene_axis(options, palette),
                "zaxis": _scene_axis(options, palette),
                "aspectmode": "data",
                "domain": {"x": [0.0, 0.88], "y": [0.0, 1.0]},
                **_camera(options.camera),
            }
        )
    else:
        axis_options = {
            "showgrid": options.show_grid,
            "gridcolor": palette["grid"],
            "gridwidth": 1,
            "showline": options.show_axes,
            "linecolor": palette["axis"],
            "linewidth": 1.2,
            "mirror": True,
            "ticks": "outside",
            "tickcolor": palette["axis"],
            "tickfont": {"color": palette["text_soft"], "size": 11},
            "title_font": {"color": palette["text"], "size": 14},
            "title_standoff": 13,
            "zeroline": options.show_grid,
            "zerolinecolor": palette["zero"],
            "zerolinewidth": 1,
            "visible": options.show_axes,
        }
        figure.update_xaxes(**axis_options)
        figure.update_yaxes(**axis_options)
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


def _scene_axis(options: PlotlyRenderOptions, palette: dict[str, str]) -> dict[str, Any]:
    return {
        "showgrid": options.show_grid,
        "gridcolor": palette["grid"],
        "linecolor": palette["axis"],
        "zerolinecolor": palette["zero"],
        "visible": options.show_axes,
        "showbackground": False,
        "tickfont": {"color": palette["text_soft"], "size": 10},
        "title_font": {"color": palette["text"], "size": 13},
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
