"""Portable display options for the Quantas Plotly renderer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class PlotlyRenderOptions:
    """GUI-level display choices that never modify scientific plot data."""

    colormap: str | None = None
    line_width: float | None = None
    line_color: str | None = None
    show_legend: bool = True
    show_grid: bool = True
    show_axes: bool = True
    axis_label_mode: Literal["cartesian", "crystal"] = "cartesian"
    show_colorbar: bool = True
    show_isolines: bool | None = None
    show_isoline_labels: bool | None = None
    contour_levels: int | None = None
    surface_opacity: float | None = None
    show_polarizations: bool = True
    polarization_stride: int = 1
    polarization_line_width: float | None = None
    polarization_scale: float | None = None
    polarization_color: str | None = None
    hover_mode: Literal["closest", "x", "x unified", "y", "y unified"] = "closest"
    projection: Literal["source", "equal_area", "stereographic"] = "source"
    camera: Literal["source", "isometric", "front", "top", "side"] = "source"
    template: Literal["quantas_dark", "plotly_white"] = "quantas_dark"
    uirevision: str | None = "quantas-result"

    def __post_init__(self) -> None:
        """Validate renderer-only numeric controls."""
        if self.line_width is not None and self.line_width <= 0.0:
            raise ValueError("line_width must be positive")
        if self.contour_levels is not None and self.contour_levels < 2:
            raise ValueError("contour_levels must be at least 2")
        if self.polarization_stride < 1:
            raise ValueError("polarization_stride must be positive")
        if self.polarization_line_width is not None and self.polarization_line_width <= 0.0:
            raise ValueError("polarization_line_width must be positive")
        if self.polarization_scale is not None and self.polarization_scale <= 0.0:
            raise ValueError("polarization_scale must be positive")


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
