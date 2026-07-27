from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from quantas_gui.renderers.plotly import PlotlyRenderOptions, plot_inventory, render_plot


@dataclass
class Axis:
    key: str
    label: str
    unit: str | None = None
    limits: tuple[float | None, float | None] | None = None


@dataclass
class Style:
    color: str | None = None
    line_style: str = "solid"
    line_width: float = 1.5
    marker: str | None = "o"
    marker_size: float | None = 5.0
    marker_edge_color: str | None = "black"
    marker_edge_width: float | None = 1.0
    alpha: float = 1.0
    errorbar_line_width: float = 1.0


@dataclass
class Series:
    key: str
    label: str
    x: np.ndarray
    y: np.ndarray
    x_error: np.ndarray | None = None
    y_error: np.ndarray | None = None
    style: Style = field(default_factory=Style)


@dataclass
class LinePlotSpec:
    key: str
    title: str
    filename_stem: str
    x_axis: Axis
    y_axis: Axis
    series: list[Series]
    bands: list[object] = field(default_factory=list)
    colored_paths: list[object] = field(default_factory=list)
    secondary_axes: list[object] = field(default_factory=list)
    spans: list[object] = field(default_factory=list)
    backgrounds: list[object] = field(default_factory=list)
    show_legend: bool = True
    invert_x_axis: bool = False
    invert_y_axis: bool = False


@dataclass
class SurfaceStyle:
    color: str | None = None
    colormap: str | None = "viridis"
    opacity: float = 1.0
    show_colorbar: bool = True
    value_limits: tuple[float, float] | None = None


@dataclass
class SurfaceLayer:
    key: str
    label: str
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    values: np.ndarray
    style: SurfaceStyle = field(default_factory=SurfaceStyle)


@dataclass
class SurfacePlotSpec:
    key: str
    title: str
    filename_stem: str
    value_axis: Axis
    layers: list[SurfaceLayer]
    vector_layers: list[object] = field(default_factory=list)
    equal_aspect: bool = True
    show_axes: bool = True


def test_line_plot_is_dispatched_to_plotly() -> None:
    spec = LinePlotSpec(
        key="line",
        title="Heat capacity",
        filename_stem="cv",
        x_axis=Axis("temperature", "Temperature", "K"),
        y_axis=Axis("cv", "C_V", "J mol^-1 K^-1"),
        series=[Series("cv", "C_V", np.array([0.0, 100.0]), np.array([0.0, 10.0]))],
    )
    figure = render_plot(spec, options=PlotlyRenderOptions())
    assert len(figure.data) == 1
    assert figure.layout.xaxis.title.text == "Temperature [K]"
    assert figure.layout.yaxis.title.text == "C_V [J mol^-1 K^-1]"


def test_surface_plot_uses_physical_values_as_customdata() -> None:
    grid = np.array([[0.0, 1.0], [0.0, 1.0]])
    values = np.array([[1.0, 2.0], [3.0, 4.0]])
    spec = SurfacePlotSpec(
        key="surface",
        title="Young modulus",
        filename_stem="young",
        value_axis=Axis("young", "Young modulus", "GPa"),
        layers=[SurfaceLayer("young", "Young modulus", grid, grid.T, values, values)],
    )
    figure = render_plot(spec)
    assert len(figure.data) == 1
    assert np.array_equal(np.asarray(figure.data[0].customdata), values)


def test_plot_inventory_remains_lightweight() -> None:
    collection = type(
        "Collection",
        (),
        {
            "plots": [
                LinePlotSpec(
                    key="line",
                    title="Line",
                    filename_stem="line",
                    x_axis=Axis("x", "X"),
                    y_axis=Axis("y", "Y"),
                    series=[],
                )
            ]
        },
    )()
    inventory = plot_inventory(collection)
    assert inventory[0].key == "line"
    assert inventory[0].kind == "LinePlotSpec"
