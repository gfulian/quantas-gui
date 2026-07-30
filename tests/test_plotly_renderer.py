from __future__ import annotations

import numpy as np
from quantas.api import plotting

from quantas_gui.renderers.plotly import PlotlyRenderOptions, plot_inventory, render_plot


def _series(
    key: str,
    label: str,
    x: np.ndarray,
    y: np.ndarray,
    *,
    color: str | None = None,
    marker: str | None = "o",
) -> plotting.PlotSeries:
    return plotting.PlotSeries(
        key=key,
        label=label,
        x=x,
        y=y,
        style=plotting.PlotSeriesStyle(
            color=color,
            marker=marker,
            marker_size=5.0,
            marker_edge_color="black",
            marker_edge_width=1.0,
        ),
    )


def test_line_plot_is_dispatched_to_plotly() -> None:
    spec = plotting.LinePlotSpec(
        key="line",
        title="Heat capacity",
        filename_stem="cv",
        x_axis=plotting.PlotAxis("temperature", "Temperature", "K"),
        y_axis=plotting.PlotAxis("cv", "C_V", "J mol^-1 K^-1"),
        series=[
            _series(
                "cv",
                "C_V",
                np.array([0.0, 100.0]),
                np.array([0.0, 10.0]),
            )
        ],
    )
    figure = render_plot(spec, options=PlotlyRenderOptions())
    assert len(figure.data) == 1
    assert figure.layout.xaxis.title.text == "Temperature (K)"
    assert figure.layout.yaxis.title.text == "C_V (J mol⁻¹ K⁻¹)"


def test_multiseries_overlay_uses_distinct_markers_for_every_series() -> None:
    x = np.asarray([0.0, 1.0, 2.0], dtype=np.float64)
    source_markers = ("o", "s", "^", "v", "D", "d", None)
    series = [
        plotting.PlotSeries(
            key=f"C{index + 1}",
            label=rf"$C_{{{index + 1}{index + 1}}}$",
            x=x + index,
            y=x,
            style=plotting.PlotSeriesStyle(marker=marker),
        )
        for index, marker in enumerate(source_markers)
    ]
    spec = plotting.LinePlotSpec(
        key="thermoelastic-overlay",
        title="Thermoelastic overlay",
        filename_stem="thermoelastic-overlay",
        x_axis=plotting.PlotAxis("stiffness", r"$C_{ij}$", "GPa"),
        y_axis=plotting.PlotAxis("depth", "Depth", "km"),
        series=series,
    )

    figure = render_plot(spec)

    symbols = [str(trace.marker.symbol) for trace in figure.data]
    assert len(symbols) == len(source_markers)
    assert len(set(symbols)) == len(source_markers)
    assert all(trace.mode == "lines+markers" for trace in figure.data)
    assert symbols[4:7] == ["diamond-wide", "diamond", "cross"]


def test_scalar_colored_overlay_uses_distinct_markers_for_every_path() -> None:
    coordinates = np.asarray([0.0, 1.0, 2.0], dtype=np.float64)
    value_axis = plotting.PlotAxis("temperature", "Temperature", "K")
    source_markers = ("o", "s", "^", "v", "D", "d", None)
    paths = [
        plotting.ColoredPathSeries(
            key=f"C{index + 1}",
            label=rf"$C_{{{index + 1}{index + 1}}}$",
            x=coordinates + index,
            y=coordinates,
            values=np.asarray([300.0, 400.0, 500.0]),
            value_axis=value_axis,
            style=plotting.ColoredPathStyle(
                marker=marker,
                show_colorbar=index == 0,
                value_limits=(300.0, 500.0),
            ),
        )
        for index, marker in enumerate(source_markers)
    ]
    spec = plotting.LinePlotSpec(
        key="thermoelastic-temperature-overlay",
        title="Thermoelastic temperature overlay",
        filename_stem="thermoelastic-temperature-overlay",
        x_axis=plotting.PlotAxis("stiffness", r"$C_{ij}$", "GPa"),
        y_axis=plotting.PlotAxis("depth", "Depth", "km"),
        series=[],
        colored_paths=paths,
    )

    figure = render_plot(spec)

    symbols = [str(trace.marker.symbol) for trace in figure.data]
    assert len(symbols) == len(source_markers)
    assert len(set(symbols)) == len(source_markers)
    assert symbols[4:7] == ["diamond-wide", "diamond", "cross"]


def test_surface_plot_uses_physical_values_as_customdata() -> None:
    grid = np.array([[0.0, 1.0], [0.0, 1.0]])
    values = np.array([[1.0, 2.0], [3.0, 4.0]])
    spec = plotting.SurfacePlotSpec(
        key="surface",
        title="Young modulus",
        filename_stem="young",
        value_axis=plotting.PlotAxis("young", "Young modulus", "GPa"),
        layers=[
            plotting.SurfaceLayer(
                "young",
                "Young modulus",
                grid,
                grid.T,
                values,
                values,
                style=plotting.SurfaceStyle(colormap="viridis"),
            )
        ],
    )
    figure = render_plot(spec)
    assert figure.data[0].type == "surface"
    assert np.array_equal(np.asarray(figure.data[0].customdata), values)
    axis_traces = [trace for trace in figure.data if trace.type == "scatter3d"]
    assert len(axis_traces) == 3
    assert [trace.text[1] for trace in axis_traces] == ["x", "y", "z"]
    assert figure.data[0].colorbar.x == 0.9


def test_plot_inventory_remains_lightweight() -> None:
    collection = plotting.PlotCollection(
        plots=[
            plotting.LinePlotSpec(
                key="line",
                title="Line",
                filename_stem="line",
                x_axis=plotting.PlotAxis("x", "X"),
                y_axis=plotting.PlotAxis("y", "Y"),
                series=[],
            )
        ]
    )
    inventory = plot_inventory(collection)
    assert inventory[0].key == "line"
    assert inventory[0].kind == "LinePlotSpec"


def test_polar_renderer_preserves_line_semantics_and_panel_identity() -> None:
    angle = np.linspace(0.0, 360.0, 37)
    panels = [
        plotting.PolarPlotPanel(
            plane,
            plane,
            [
                _series(
                    f"young_{plane}",
                    "Young's modulus",
                    angle,
                    1.0 + 0.2 * np.cos(np.radians(angle)),
                    color="#009010",
                    marker=None,
                )
            ],
        )
        for plane in ("xy", "xz", "yz")
    ]
    figure = render_plot(plotting.PolarPlotSpec("young", "Young's modulus", "young", panels))
    assert len(figure.data) == 3
    assert all(trace.mode == "lines" for trace in figure.data)
    assert [annotation.text for annotation in figure.layout.annotations] == ["xy", "xz", "yz"]
    assert list(figure.layout.polar.angularaxis.ticktext) == ["+x", "+y", "−x", "−y"]
    assert figure.layout.height >= 640


def test_polar_renderer_supports_crystallographic_principal_plane_labels() -> None:
    angle = np.linspace(0.0, 360.0, 13)
    panel = plotting.PolarPlotPanel(
        "xz",
        "xz",
        [_series("young", "Young modulus", angle, np.ones_like(angle), marker=None)],
        metadata={"plane": "xz"},
    )
    figure = render_plot(
        plotting.PolarPlotSpec("young-xz", "Young modulus", "young-xz", [panel]),
        options=PlotlyRenderOptions(axis_label_mode="crystal"),
    )
    assert list(figure.layout.polar.angularaxis.ticktext) == [
        "[001]",
        "[100]",
        "[00−1]",
        "[−100]",
    ]


def test_spherical_renderer_uses_a_continuous_projected_contour() -> None:
    theta = np.linspace(0.0, 0.5 * np.pi, 15)
    phi = np.linspace(0.0, 2.0 * np.pi, 24, endpoint=False)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    values = np.sin(theta_grid) ** 2 * np.cos(2.0 * phi_grid)
    spec = plotting.SphericalMapSpec(
        key="vp",
        title="Compressional velocity",
        filename_stem="vp",
        theta=theta,
        phi=phi,
        values=values,
        value_axis=plotting.PlotAxis("vp", r"$V_P$ (km s$^{-1}$)", "km s^-1"),
        hemisphere="upper",
        metadata={"color_center": 0.0},
    )
    figure = render_plot(spec)
    assert [trace.type for trace in figure.data] == ["contour", "contour"]
    assert figure.data[0].type == "contour"
    assert np.asarray(figure.data[0].z).ndim == 2
    assert figure.data[0].colorbar.title.text == r"$V_P$ (km s⁻¹)"
    assert figure.data[0].colorbar.title.side == "top"
    assert figure.data[0].colorbar.orientation == "h"
    assert figure.data[0].colorbar.y < 0.0
    assert figure.layout.paper_bgcolor == "rgba(0, 0, 0, 0)"


def test_complete_math_axis_label_does_not_duplicate_its_unit() -> None:
    spec = plotting.LinePlotSpec(
        key="velocity",
        title="Velocity",
        filename_stem="velocity",
        x_axis=plotting.PlotAxis("pressure", r"$P$ (GPa)", "GPa"),
        y_axis=plotting.PlotAxis("vp", r"$V_P$ (km s$^{-1}$)", "km s^-1"),
        series=[
            _series(
                "vp",
                r"$V_P$",
                np.array([0.0, 1.0]),
                np.array([8.0, 8.1]),
            )
        ],
    )
    figure = render_plot(spec)
    assert figure.layout.xaxis.title.text == r"$P$ (GPa)"
    assert figure.layout.yaxis.title.text == r"$V_P$ (km s⁻¹)"


def test_spherical_renderer_projects_axial_overlays() -> None:
    theta = np.linspace(0.0, 0.5 * np.pi, 9)
    phi = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    directions = np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    spec = plotting.SphericalMapSpec(
        key="polarization",
        title="Polarization",
        filename_stem="polarization",
        theta=theta,
        phi=phi,
        values=np.cos(theta_grid) + 0.1 * np.cos(phi_grid),
        value_axis=plotting.PlotAxis("value", "Value"),
        hemisphere="upper",
        axis_layers=[
            plotting.AxisFieldLayer(
                key="axis",
                label="Polarization axis",
                directions=directions,
                axes=np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]]),
            )
        ],
    )
    figure = render_plot(spec, options=PlotlyRenderOptions(template="quantas_dark"))
    assert [trace.type for trace in figure.data] == ["contour", "contour", "scatter"]
    assert figure.data[2].mode == "lines"
    assert figure.data[2].line.color == "#ecf5fb"


def test_plot_inventory_exposes_plot_kind_specific_controls() -> None:
    contour = plotting.ContourPlotSpec(
        key="contour",
        title="Contour",
        filename_stem="contour",
        x=np.asarray([0.0, 1.0]),
        y=np.asarray([0.0, 1.0]),
        z=np.asarray([[0.0, 1.0], [1.0, 2.0]]),
        x_axis=plotting.PlotAxis("x", "X"),
        y_axis=plotting.PlotAxis("y", "Y"),
        value_axis=plotting.PlotAxis("value", "Value"),
    )
    inventory = plot_inventory(plotting.PlotCollection(plots=[contour]))
    controls = inventory[0].controls
    assert controls.colormap
    assert controls.colorbar
    assert controls.contour
    assert controls.line_style
    assert not controls.surface


def test_line_style_overrides_are_presentation_only() -> None:
    spec = plotting.LinePlotSpec(
        key="line-style",
        title="Styled line",
        filename_stem="styled-line",
        x_axis=plotting.PlotAxis("x", "Pressure", "GPa"),
        y_axis=plotting.PlotAxis("y", "Velocity", "km s^-1"),
        series=[_series("vp", r"$V_P$", np.array([0.0, 1.0]), np.array([8.0, 8.1]))],
    )
    figure = render_plot(
        spec,
        options=PlotlyRenderOptions(line_width=3.5, line_color="#f06c75"),
    )
    assert figure.data[0].line.width == 3.5
    assert figure.data[0].line.color == "#f06c75"
    assert figure.layout.xaxis.title.text == "Pressure (GPa)"
    assert figure.layout.yaxis.title.text == "Velocity (km s⁻¹)"


def test_contour_count_and_line_style_are_overridable() -> None:
    spec = plotting.ContourPlotSpec(
        key="contour-controls",
        title="Contour controls",
        filename_stem="contour-controls",
        x=np.asarray([0.0, 1.0]),
        y=np.asarray([0.0, 1.0]),
        z=np.asarray([[0.0, 1.0], [1.0, 2.0]]),
        x_axis=plotting.PlotAxis("pressure", "Pressure", "GPa"),
        y_axis=plotting.PlotAxis("temperature", "Temperature", "K"),
        value_axis=plotting.PlotAxis("volume", "Volume", "A^3"),
    )
    figure = render_plot(
        spec,
        options=PlotlyRenderOptions(
            contour_levels=17,
            line_width=2.25,
            line_color="#ed8a28",
        ),
    )
    assert figure.data[0].ncontours == 17
    assert figure.data[0].line.width == 2.25
    assert figure.data[0].line.color == "#ed8a28"
    assert figure.data[0].colorbar.title.text == "Volume (Å³)"


def test_spherical_axes_and_polarization_controls() -> None:
    theta = np.linspace(0.0, 0.5 * np.pi, 9)
    phi = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    directions = np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [-1.0, 0.0, 1.0], [0.0, -1.0, 1.0]])
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    spec = plotting.SphericalMapSpec(
        key="controlled-polarization",
        title="Controlled polarization",
        filename_stem="controlled-polarization",
        theta=theta,
        phi=phi,
        values=np.cos(theta_grid) + 0.1 * np.cos(phi_grid),
        value_axis=plotting.PlotAxis("vs", r"$V_S$", "km s^-1"),
        hemisphere="upper",
        axis_layers=[
            plotting.AxisFieldLayer(
                key="axis",
                label="Polarization axis",
                directions=directions,
                axes=np.tile(np.array([[0.0, 1.0, 0.0]]), (4, 1)),
            )
        ],
    )
    figure = render_plot(
        spec,
        options=PlotlyRenderOptions(
            axis_label_mode="crystal",
            contour_levels=9,
            polarization_stride=2,
            polarization_line_width=2.5,
            polarization_color="#f0b75a",
        ),
    )
    annotations = {annotation.text for annotation in figure.layout.annotations}
    assert {"[100]", "[−100]", "[010]", "[0−10]", "[001]"} <= annotations
    overlay = figure.data[-1]
    assert overlay.type == "scatter"
    assert overlay.line.width == 2.5
    assert overlay.line.color == "#f0b75a"
    assert list(overlay.x).count(None) == 2
    assert figure.data[1].ncontours == 9


def test_surface_crystallographic_axes_and_polarization_toggle() -> None:
    grid = np.array([[-1.0, 1.0], [-1.0, 1.0]])
    values = np.ones((2, 2))
    vector_layer = plotting.VectorFieldLayer(
        key="polarization",
        label="Polarization",
        origins=np.array([[0.0, 0.0, 1.0]]),
        vectors=np.array([[1.0, 0.0, 0.0]]),
        axial=True,
    )
    spec = plotting.SurfacePlotSpec(
        key="surface-axes",
        title="Surface axes",
        filename_stem="surface-axes",
        value_axis=plotting.PlotAxis("vp", r"$V_P$", "km s^-1"),
        layers=[
            plotting.SurfaceLayer(
                "vp",
                "VP",
                grid,
                grid.T,
                values,
                values,
                style=plotting.SurfaceStyle(colormap="viridis"),
            )
        ],
        vector_layers=[vector_layer],
    )
    figure = render_plot(
        spec,
        options=PlotlyRenderOptions(
            axis_label_mode="crystal",
            show_polarizations=False,
        ),
    )
    assert not any(trace.name == "Polarization" for trace in figure.data)
    axes = [trace for trace in figure.data if trace.type == "scatter3d"]
    assert [trace.text[1] for trace in axes] == ["[100]", "[010]", "[001]"]


def test_inventory_exposes_polarization_controls_only_when_layers_exist() -> None:
    theta = np.linspace(0.0, 0.5 * np.pi, 3)
    phi = np.linspace(0.0, 2.0 * np.pi, 4, endpoint=False)
    values = np.ones((3, 4))
    base = dict(
        title="Map",
        filename_stem="map",
        theta=theta,
        phi=phi,
        values=values,
        value_axis=plotting.PlotAxis("value", "Value"),
        hemisphere="upper",
    )
    plain = plotting.SphericalMapSpec(key="plain", **base)
    layered = plotting.SphericalMapSpec(
        key="layered",
        axis_layers=[
            plotting.AxisFieldLayer(
                "axis",
                "Axis",
                np.array([[0.0, 0.0, 1.0]]),
                np.array([[1.0, 0.0, 0.0]]),
            )
        ],
        **base,
    )
    inventory = plot_inventory(plotting.PlotCollection(plots=[plain, layered]))
    assert not inventory[0].controls.polarization
    assert inventory[1].controls.polarization


def test_contour_override_uses_exact_levels_and_replaces_source_levels() -> None:
    spec = plotting.ContourPlotSpec(
        key="exact-contours",
        title="Exact contours",
        filename_stem="exact-contours",
        x=np.asarray([0.0, 1.0]),
        y=np.asarray([0.0, 1.0]),
        z=np.asarray([[0.0, 1.0], [1.0, 2.0]]),
        x_axis=plotting.PlotAxis("x", "X"),
        y_axis=plotting.PlotAxis("y", "Y"),
        value_axis=plotting.PlotAxis("value", "Value"),
        levels=30,
    )
    source = render_plot(spec)
    reduced = render_plot(spec, options=PlotlyRenderOptions(contour_levels=10))

    assert source.data[0].ncontours == 30
    assert reduced.data[0].ncontours == 10
    assert reduced.data[0].autocontour is False
    start = float(reduced.data[0].contours.start)
    end = float(reduced.data[0].contours.end)
    size = float(reduced.data[0].contours.size)
    assert round((end - start) / size) + 1 == 10
    assert len(reduced.data) == 1


def test_spherical_isoline_override_contains_only_the_requested_line_set() -> None:
    theta = np.linspace(0.0, 0.5 * np.pi, 9)
    phi = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    spec = plotting.SphericalMapSpec(
        key="exact-spherical-contours",
        title="Exact spherical contours",
        filename_stem="exact-spherical-contours",
        theta=theta,
        phi=phi,
        values=np.cos(theta_grid) + np.cos(phi_grid),
        value_axis=plotting.PlotAxis("value", "Value"),
        hemisphere="upper",
        levels=30,
    )
    figure = render_plot(spec, options=PlotlyRenderOptions(contour_levels=10))
    line_traces = [
        trace
        for trace in figure.data
        if trace.type == "contour" and trace.contours.coloring == "none"
    ]
    assert len(line_traces) == 1
    assert line_traces[0].ncontours == 10
    assert line_traces[0].autocontour is False
    start = float(line_traces[0].contours.start)
    end = float(line_traces[0].contours.end)
    size = float(line_traces[0].contours.size)
    assert round((end - start) / size) + 1 == 10


def test_surface_polarization_overlay_matches_matplotlib_relative_scaling() -> None:
    grid = np.array([[-2.0, 2.0], [-2.0, 2.0]])
    values = np.ones((2, 2))
    vector_layer = plotting.VectorFieldLayer(
        key="polarization",
        label="Polarization",
        origins=np.array([[0.0, 0.0, 1.0]]),
        vectors=np.array([[4.0, 0.0, 0.0]]),
        axial=True,
        style=plotting.VectorFieldStyle(color="black", scale=0.08),
    )
    spec = plotting.SurfacePlotSpec(
        key="surface-polarization",
        title="Surface polarization",
        filename_stem="surface-polarization",
        value_axis=plotting.PlotAxis("vp", r"$V_P$", "km s^-1"),
        layers=[
            plotting.SurfaceLayer(
                "vp",
                "VP",
                grid,
                grid.T,
                values,
                values,
                style=plotting.SurfaceStyle(colormap="viridis"),
            )
        ],
        vector_layers=[vector_layer],
    )
    figure = render_plot(
        spec,
        options=PlotlyRenderOptions(
            template="quantas_dark",
            polarization_scale=0.10,
            polarization_line_width=2.0,
        ),
    )
    overlay = next(trace for trace in figure.data if trace.name == "Polarization")
    coordinates = [value for value in overlay.x if value is not None]
    assert np.isclose(abs(coordinates[1] - coordinates[0]), 0.2)
    assert overlay.line.width == 2.0
    assert overlay.line.color == "#ecf5fb"


def test_matplotlib_grayscale_colors_are_translated_for_plotly() -> None:
    x = np.asarray([0.0, 1.0], dtype=np.float64)
    spec = plotting.LinePlotSpec(
        key="grayscale",
        title="Portable grayscale",
        filename_stem="portable-grayscale",
        x_axis=plotting.PlotAxis("x", "Volume", "A^3"),
        y_axis=plotting.PlotAxis("y", "Stiffness", "GPa"),
        series=[
            plotting.PlotSeries(
                key="fit",
                label="Fit",
                x=x,
                y=np.asarray([10.0, 11.0], dtype=np.float64),
                style=plotting.PlotSeriesStyle(
                    color="0.35",
                    marker="o",
                    marker_edge_color="0.65",
                ),
            )
        ],
        bands=[
            plotting.PlotBand(
                key="confidence",
                label="Confidence",
                coordinates=x,
                lower=np.asarray([9.8, 10.8], dtype=np.float64),
                upper=np.asarray([10.2, 11.2], dtype=np.float64),
                style=plotting.PlotBandStyle(color="0.65", alpha=0.25),
            )
        ],
    )

    figure = render_plot(spec)

    assert figure.data[1].fillcolor == "rgba(166,166,166,0.25)"
    assert figure.data[2].line.color == "#595959"
    assert figure.data[2].marker.line.color == "#a6a6a6"


def test_panel_plot_accepts_frontend_neutral_grayscale_styles() -> None:
    x = np.asarray([0.0, 1.0], dtype=np.float64)
    child = plotting.LinePlotSpec(
        key="thermo-fit",
        title="Elastic-volume fit",
        filename_stem="elastic-volume-fit",
        x_axis=plotting.PlotAxis("volume", "Volume", "A^3"),
        y_axis=plotting.PlotAxis("stiffness", "C_11", "GPa"),
        series=[
            plotting.PlotSeries(
                key="observed",
                label="Observed",
                x=x,
                y=np.asarray([100.0, 98.0], dtype=np.float64),
                style=plotting.PlotSeriesStyle(color="0.35", marker="o"),
            )
        ],
    )
    spec = plotting.PanelPlotSpec(
        key="thermoelastic-fit",
        title="Elastic-volume calibration fits",
        filename_stem="thermoelastic-fit",
        panels=[child],
    )

    figure = render_plot(spec)

    assert len(figure.data) == 1
    assert figure.data[0].line.color == "#595959"


def test_panel_plot_deduplicates_shared_scalar_colorbars() -> None:
    coordinates = np.asarray([0.0, 1.0, 2.0], dtype=np.float64)
    value_axis = plotting.PlotAxis("temperature", "Temperature (K)", "K")
    panels = []
    for index in range(2):
        panels.append(
            plotting.LinePlotSpec(
                key=f"profile-{index}",
                title=f"$C_{{{index + 1}{index + 1}}}$",
                filename_stem=f"profile-{index}",
                x_axis=plotting.PlotAxis(
                    "stiffness",
                    r"Elastic stiffness $C_{IJ}$ (GPa)",
                    "GPa",
                ),
                y_axis=plotting.PlotAxis("depth", "Depth (km)", "km"),
                series=[],
                colored_paths=[
                    plotting.ColoredPathSeries(
                        key=f"path-{index}",
                        label=f"$C_{{{index + 1}{index + 1}}}$",
                        x=coordinates + index,
                        y=coordinates,
                        values=np.asarray([300.0, 500.0, 700.0]),
                        value_axis=value_axis,
                        style=plotting.ColoredPathStyle(
                            show_colorbar=True,
                            value_limits=(300.0, 700.0),
                        ),
                    )
                ],
                invert_y_axis=True,
            )
        )
    spec = plotting.PanelPlotSpec(
        key="profiles",
        title="Thermoelastic profiles",
        filename_stem="profiles",
        panels=panels,
        columns=2,
        share_y=True,
    )

    figure = render_plot(spec)

    visible_colorbars = [
        trace
        for trace in figure.data
        if bool(getattr(getattr(trace, "marker", None), "showscale", False))
    ]
    assert len(visible_colorbars) == 1
    assert figure.layout.xaxis.title.text == r"Elastic stiffness $C_{ij}$ (GPa)"
    assert figure.layout.yaxis.autorange == "reversed"
    assert figure.layout.margin.r >= 140


def test_panel_plot_keeps_colorbars_with_distinct_scalar_ranges() -> None:
    coordinates = np.asarray([0.0, 1.0, 2.0], dtype=np.float64)
    value_axis = plotting.PlotAxis("temperature", "Temperature (K)", "K")
    panels = []
    for index, limits in enumerate(((300.0, 700.0), (500.0, 900.0))):
        panels.append(
            plotting.LinePlotSpec(
                key=f"range-{index}",
                title=f"Range {index + 1}",
                filename_stem=f"range-{index}",
                x_axis=plotting.PlotAxis("value", "Value", None),
                y_axis=plotting.PlotAxis("depth", "Depth (km)", "km"),
                series=[],
                colored_paths=[
                    plotting.ColoredPathSeries(
                        key=f"path-{index}",
                        label=f"Path {index + 1}",
                        x=coordinates,
                        y=coordinates,
                        values=np.asarray(limits)[[0, 0, 1]],
                        value_axis=value_axis,
                        style=plotting.ColoredPathStyle(
                            show_colorbar=True,
                            value_limits=limits,
                        ),
                    )
                ],
            )
        )
    spec = plotting.PanelPlotSpec(
        key="different-ranges",
        title="Distinct ranges",
        filename_stem="different-ranges",
        panels=panels,
        columns=2,
    )

    figure = render_plot(spec)

    visible_colorbars = [
        trace
        for trace in figure.data
        if bool(getattr(getattr(trace, "marker", None), "showscale", False))
    ]
    assert len(visible_colorbars) == 2


def test_contour_colored_path_uses_default_marker_when_backend_omits_one() -> None:
    coordinates = np.asarray([0.0, 1.0, 2.0], dtype=np.float64)
    path = plotting.ColoredPathSeries(
        key="profile",
        label="Archived profile",
        x=coordinates,
        y=coordinates,
        values=np.asarray([300.0, 400.0, 500.0]),
        value_axis=plotting.PlotAxis("temperature", "Temperature", "K"),
        style=plotting.ColoredPathStyle(marker=None, show_colorbar=False),
    )
    spec = plotting.ContourPlotSpec(
        key="domain-with-profile",
        title="Domain with archived profile",
        filename_stem="domain-with-profile",
        x_axis=plotting.PlotAxis("pressure", "Pressure", "GPa"),
        y_axis=plotting.PlotAxis("temperature", "Temperature", "K"),
        value_axis=plotting.PlotAxis("volume", "Equilibrium volume", "A^3"),
        x=np.asarray([0.0, 1.0, 2.0]),
        y=np.asarray([300.0, 400.0, 500.0]),
        z=np.asarray(
            [
                [60.0, 59.0, 58.0],
                [61.0, 60.0, 59.0],
                [62.0, 61.0, 60.0],
            ]
        ),
        colored_paths=[path],
    )

    figure = render_plot(spec)

    assert len(figure.data) == 2
    assert figure.data[1].marker.symbol == "circle"
