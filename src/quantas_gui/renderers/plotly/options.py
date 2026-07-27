"""Portable display options for the Quantas Plotly renderer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class PlotlyRenderOptions:
    """GUI-level display choices that never modify scientific plot data."""

    colormap: str | None = None
    show_legend: bool = True
    show_grid: bool = True
    show_axes: bool = True
    show_colorbar: bool = True
    show_isolines: bool | None = None
    show_isoline_labels: bool | None = None
    surface_opacity: float | None = None
    hover_mode: Literal["closest", "x", "x unified", "y", "y unified"] = "closest"
    projection: Literal["source", "equal_area", "stereographic"] = "source"
    camera: Literal["source", "isometric", "front", "top", "side"] = "source"
    template: Literal["quantas_dark", "plotly_white"] = "quantas_dark"
    uirevision: str | None = "quantas-result"


COLORMAP_OPTIONS: tuple[tuple[str, str], ...] = (
    ("From result", "source"),
    ("Viridis", "viridis"),
    ("Cividis", "cividis"),
    ("Plasma", "plasma"),
    ("Inferno", "inferno"),
    ("Magma", "magma"),
    ("Turbo", "turbo"),
    ("Blue–red", "rdbu"),
    ("Spectral", "spectral"),
)
