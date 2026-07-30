"""Plotly dispatcher for public Quantas ``PlotCollection`` specifications."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from math import pi
from types import ModuleType
from typing import Any, TypeAlias

import numpy as np
import plotly.graph_objects as go
from numpy.typing import NDArray
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots

from quantas_gui.presentation.scientific_labels import (
    scientific_label_text,
    scientific_math_label,
)
from quantas_gui.renderers.plotly.common import (
    apply_layout,
    array,
    axis_title,
    colorbar_options,
    colorscale,
    distinct_series_marker,
    limits,
    line_dash,
    marker_symbol,
    portable_color,
    series_color,
    subplot_grid,
    theme_palette,
)
from quantas_gui.renderers.plotly.options import PlotlyRenderOptions

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]


@dataclass(frozen=True, slots=True)
class PlotControlProfile:
    """Controls applicable to one plot specification family."""

    colormap: bool = False
    hover: bool = True
    projection: bool = False
    contour: bool = False
    surface: bool = False
    colorbar: bool = False
    line_style: bool = False
    axis_labels: bool = False
    polarization: bool = False
    legend: bool = True
    grid: bool = True
    axes: bool = True

    def as_dict(self) -> dict[str, bool]:
        """Return a JSON-safe control profile."""
        return {name: bool(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True)
class PlotDescriptor:
    """Lightweight module-aware plot inventory entry safe for browser storage."""

    key: str
    title: str
    kind: str
    family_key: str = "default"
    group: str = "Figures"
    description: str = ""
    controls: PlotControlProfile = PlotControlProfile()

    def as_option(self) -> dict[str, str]:
        """Return one Dash-dropdown option."""
        return {
            "label": scientific_label_text(f"{self.group} · {self.title}"),
            "value": self.key,
        }

    def as_dict(self) -> dict[str, Any]:
        """Return a bounded JSON-safe descriptor."""
        return {
            "key": self.key,
            "title": self.title,
            "kind": self.kind,
            "family_key": self.family_key,
            "group": self.group,
            "description": self.description,
            "controls": self.controls.as_dict(),
        }


def plot_inventory(
    collection: Any,
    *,
    family_key: str = "default",
    group_resolver: Any | None = None,
    description_resolver: Any | None = None,
) -> tuple[PlotDescriptor, ...]:
    """Return stable module-aware metadata for a plot collection."""
    descriptors: list[PlotDescriptor] = []
    seen: set[str] = set()
    for index, spec in enumerate(getattr(collection, "plots", ())):
        key = str(getattr(spec, "key", f"plot-{index + 1}"))
        if key in seen:
            key = f"{key}-{index + 1}"
        seen.add(key)
        title = str(getattr(spec, "title", key))
        kind, _ = _typed_renderer(spec)
        descriptors.append(
            PlotDescriptor(
                key=key,
                title=title,
                kind=kind,
                family_key=family_key,
                group=(group_resolver(title, kind, family_key) if group_resolver else "Figures"),
                description=(
                    description_resolver(title, kind, family_key) if description_resolver else ""
                ),
                controls=_control_profile(kind, spec),
            )
        )
    return tuple(descriptors)


def render_plot(
    spec: Any,
    *,
    options: PlotlyRenderOptions | None = None,
) -> go.Figure:
    """Render one public Quantas plot specification with Plotly."""
    resolved = options or PlotlyRenderOptions()
    _, renderer = _typed_renderer(spec)
    return renderer(spec, resolved)


@lru_cache(maxsize=1)
def _public_plotting() -> ModuleType:
    """Import the public PlotSpec namespace only when scientific rendering starts."""
    return import_module("quantas.api.plotting")


def _typed_renderer(spec: Any) -> tuple[str, Any]:
    """Resolve one renderer using public Quantas PlotSpec classes."""
    plotting = _public_plotting()
    dispatch = (
        ("LinePlotSpec", plotting.LinePlotSpec, _line_plot),
        ("ContourPlotSpec", plotting.ContourPlotSpec, _contour_plot),
        ("PolarPlotSpec", plotting.PolarPlotSpec, _polar_plot),
        ("SurfacePlotSpec", plotting.SurfacePlotSpec, _surface_plot),
        ("SphericalMapSpec", plotting.SphericalMapSpec, _spherical_map),
        (
            "SphericalSummarySpec",
            plotting.SphericalSummarySpec,
            _spherical_summary,
        ),
        ("PanelPlotSpec", plotting.PanelPlotSpec, _panel_plot),
    )
    for kind, spec_type, renderer in dispatch:
        if isinstance(spec, spec_type):
            return kind, renderer
    class_name = spec.__class__.__name__
    raise TypeError(f"unsupported Quantas plot specification {class_name!r}")


def render_collection_plot(
    collection: Any,
    key: str,
    *,
    options: PlotlyRenderOptions | None = None,
) -> go.Figure:
    """Render one plot selected by its stable key from a collection."""
    for spec in getattr(collection, "plots", ()):
        if str(getattr(spec, "key", "")) == str(key):
            return render_plot(spec, options=options)
    raise KeyError(f"plot collection has no plot {key!r}")


def _line_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    figure = go.Figure()
    for background in getattr(spec, "backgrounds", ()):
        _add_scalar_background(figure, background, override_colormap=options.colormap)
    for band_index, band in enumerate(getattr(spec, "bands", ())):
        coordinates = array(band.coordinates)
        lower = array(band.lower)
        upper = array(band.upper)
        style = band.style
        color = series_color(band_index, getattr(style, "color", None))
        if getattr(band, "orientation", "vertical") == "horizontal":
            figure.add_trace(
                go.Scatter(
                    x=lower,
                    y=coordinates,
                    mode="lines",
                    line={"width": 0},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            figure.add_trace(
                go.Scatter(
                    x=upper,
                    y=coordinates,
                    mode="lines",
                    fill="tonextx",
                    fillcolor=_rgba(color, float(getattr(style, "alpha", 0.2))),
                    line={"width": float(getattr(style, "edge_width", 0.0)), "color": color},
                    name=scientific_math_label(band.label),
                    hoverinfo="skip",
                )
            )
        else:
            figure.add_trace(
                go.Scatter(
                    x=coordinates,
                    y=lower,
                    mode="lines",
                    line={"width": 0},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            figure.add_trace(
                go.Scatter(
                    x=coordinates,
                    y=upper,
                    mode="lines",
                    fill="tonexty",
                    fillcolor=_rgba(color, float(getattr(style, "alpha", 0.2))),
                    line={"width": float(getattr(style, "edge_width", 0.0)), "color": color},
                    name=scientific_math_label(band.label),
                    hoverinfo="skip",
                )
            )

    series_items = tuple(getattr(spec, "series", ()))
    colored_paths = tuple(getattr(spec, "colored_paths", ()))
    source_markers = tuple(
        getattr(item.style, "marker", None) for item in (*series_items, *colored_paths)
    )
    diversify_markers = len(source_markers) > 1 and any(
        marker is not None for marker in source_markers
    )
    used_markers: set[str] = set()

    for index, series in enumerate(series_items):
        requested_marker = getattr(series.style, "marker", None)
        resolved_marker = (
            distinct_series_marker(index, requested_marker, used_markers)
            if diversify_markers
            else marker_symbol(requested_marker)
            if requested_marker is not None
            else None
        )
        _add_cartesian_series(
            figure,
            series,
            index=index,
            marker=resolved_marker,
            options=options,
        )

    marker_offset = len(series_items)
    for index, path in enumerate(colored_paths):
        requested_marker = getattr(path.style, "marker", None)
        resolved_marker = (
            distinct_series_marker(marker_offset + index, requested_marker, used_markers)
            if len(source_markers) > 1
            else marker_symbol(requested_marker)
        )
        _add_colored_path(
            figure,
            path,
            index=index,
            marker=resolved_marker,
            override_colormap=options.colormap,
            options=options,
        )

    for span in getattr(spec, "spans", ()):
        color = portable_color(getattr(span, "color", None), "#7f9bad")
        arguments = {
            "fillcolor": color,
            "opacity": float(getattr(span, "alpha", 0.25)),
            "line_width": 0,
            "layer": "below",
            "annotation_text": scientific_math_label(getattr(span, "label", "")),
            "annotation_position": "top left",
        }
        if getattr(span, "axis", "x") == "y":
            figure.add_hrect(y0=float(span.start), y1=float(span.end), **arguments)
        else:
            figure.add_vrect(x0=float(span.start), x1=float(span.end), **arguments)

    figure.update_xaxes(title_text=axis_title(spec.x_axis))
    figure.update_yaxes(title_text=axis_title(spec.y_axis))
    _add_secondary_axes(figure, getattr(spec, "secondary_axes", ()))
    _apply_axis_limits(figure, spec.x_axis, axis="x")
    _apply_axis_limits(figure, spec.y_axis, axis="y")
    if bool(getattr(spec, "invert_x_axis", False)):
        figure.update_xaxes(autorange="reversed")
    if bool(getattr(spec, "invert_y_axis", False)):
        figure.update_yaxes(autorange="reversed")
    figure = apply_layout(
        figure,
        title=scientific_math_label(spec.title),
        options=_merge_options(options, show_legend=bool(getattr(spec, "show_legend", True))),
    )
    if options.show_colorbar and any(
        bool(getattr(path.style, "show_colorbar", True))
        for path in getattr(spec, "colored_paths", ())
    ):
        figure.update_layout(margin={"l": 82, "r": 138, "t": 76, "b": 74})
    return figure


def _contour_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    figure = go.Figure()
    lower, upper = limits(getattr(spec, "value_limits", None))
    selected_colormap = options.colormap or getattr(spec, "colormap", "viridis")
    show_lines = (
        bool(getattr(spec, "isolines", True))
        if options.show_isolines is None
        else options.show_isolines
    )
    show_labels = (
        bool(getattr(spec, "isoline_labels", False))
        if options.show_isoline_labels is None
        else options.show_isoline_labels
    )
    palette = theme_palette(options)
    level_count = options.contour_levels or int(getattr(spec, "levels", 12))
    contour_levels = _exact_contour_levels(
        array(spec.z),
        count=level_count,
        lower=lower,
        upper=upper,
    )
    contour = go.Contour(
        x=array(spec.x),
        y=array(spec.y),
        z=array(spec.z),
        colorscale=colorscale(selected_colormap),
        zmin=lower,
        zmax=upper,
        autocontour=contour_levels["autocontour"],
        ncontours=level_count,
        contours={
            "coloring": "heatmap" if getattr(spec, "mode", "smooth") == "smooth" else "fill",
            "showlines": show_lines,
            "showlabels": show_labels,
            **contour_levels["contours"],
        },
        line={
            "color": portable_color(options.line_color, palette["axis"]),
            "width": options.line_width or 0.7,
        },
        showscale=options.show_colorbar,
        colorbar=colorbar_options(spec.value_axis),
        hovertemplate=(
            f"{axis_title(spec.x_axis)}: %{{x:.6g}}<br>"
            f"{axis_title(spec.y_axis)}: %{{y:.6g}}<br>"
            f"{axis_title(spec.value_axis)}: %{{z:.6g}}<extra></extra>"
        ),
    )
    if getattr(spec, "center", None) is not None:
        contour.update(zmid=float(spec.center))
    figure.add_trace(contour)

    for mask in getattr(spec, "masks", ()):
        mask_values = np.where(array(mask.mask), 1.0, np.nan)
        figure.add_trace(
            go.Contour(
                x=array(mask.x),
                y=array(mask.y),
                z=mask_values,
                colorscale=[
                    [0.0, "rgba(240,108,117,0.12)"],
                    [1.0, "rgba(240,108,117,0.12)"],
                ],
                showscale=False,
                contours={"coloring": "fill", "showlines": False},
                hoverinfo="skip",
                name=scientific_math_label(mask.label),
            )
        )

    for index, series in enumerate(getattr(spec, "series", ())):
        _add_cartesian_series(
            figure,
            series,
            index=index,
            marker=marker_symbol(getattr(series.style, "marker", None)),
            options=options,
        )
    for index, path in enumerate(getattr(spec, "colored_paths", ())):
        _add_colored_path(
            figure,
            path,
            index=index,
            marker=marker_symbol(getattr(path.style, "marker", None)),
            override_colormap=options.colormap,
            options=options,
        )

    figure.update_xaxes(title_text=axis_title(spec.x_axis))
    figure.update_yaxes(title_text=axis_title(spec.y_axis))
    _apply_axis_limits(figure, spec.x_axis, axis="x")
    _apply_axis_limits(figure, spec.y_axis, axis="y")
    figure = apply_layout(
        figure,
        title=scientific_math_label(spec.title),
        options=options,
    )
    if options.show_colorbar:
        figure.update_layout(margin={"l": 82, "r": 142, "t": 76, "b": 74})
    return figure


def _polar_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    """Render a Matplotlib-equivalent multi-plane polar line figure."""
    panels = list(getattr(spec, "panels", ()))
    if not panels:
        raise ValueError("a polar plot requires at least one panel")

    columns = min(3, len(panels))
    rows, columns = subplot_grid(len(panels), columns)
    figure = make_subplots(
        rows=rows,
        cols=columns,
        specs=[[{"type": "polar"} for _ in range(columns)] for _ in range(rows)],
        subplot_titles=[str(panel.title) for panel in panels],
        horizontal_spacing=0.06,
        vertical_spacing=0.16,
    )
    palette = theme_palette(options)
    legend_labels: set[str] = set()

    for panel_index, panel in enumerate(panels):
        row = panel_index // columns + 1
        column = panel_index % columns + 1
        for series_index, series in enumerate(panel.series):
            style = series.style
            marker = getattr(style, "marker", None)
            mode = "lines+markers" if marker is not None else "lines"
            theta = array(series.x)
            theta_unit = str(getattr(panel, "angle_unit", "degree"))
            if theta_unit == "radian":
                theta = np.degrees(theta)
            label = str(series.label)
            color = series_color(series_index, options.line_color or getattr(style, "color", None))
            show_legend = label not in legend_labels
            legend_labels.add(label)
            figure.add_trace(
                go.Scatterpolar(
                    theta=theta,
                    r=array(series.y),
                    thetaunit="degrees",
                    mode=mode,
                    name=label,
                    legendgroup=label,
                    showlegend=show_legend,
                    opacity=float(getattr(style, "alpha", 1.0)),
                    line={
                        "color": color,
                        "width": options.line_width or float(getattr(style, "line_width", 1.5)),
                        "dash": line_dash(getattr(style, "line_style", "solid")),
                    },
                    marker={
                        "symbol": marker_symbol(marker),
                        "size": float(getattr(style, "marker_size", 6.0) or 6.0),
                        "color": color,
                        "line": {
                            "color": portable_color(
                                getattr(style, "marker_edge_color", None), palette["axis"]
                            ),
                            "width": float(getattr(style, "marker_edge_width", 0.0) or 0.0),
                        },
                    },
                    hovertemplate=(
                        f"{panel.title}<br>{label}<br>"
                        "angle: %{theta:.3f}°<br>value: %{r:.7g}<extra></extra>"
                    ),
                ),
                row=row,
                col=column,
            )

        polar_name = "polar" if panel_index == 0 else f"polar{panel_index + 1}"
        radial_limit = getattr(panel, "radial_limit", None)
        figure.layout[polar_name].update(
            radialaxis={
                "range": None if radial_limit is None else [0.0, float(radial_limit)],
                "showgrid": bool(getattr(panel, "grid", True)) and options.show_grid,
                "gridcolor": palette["grid"],
                "gridwidth": 1,
                "showline": options.show_axes,
                "linecolor": palette["axis"],
                "linewidth": 1.2,
                "tickfont": {"color": palette["text_soft"], "size": 10},
                "angle": 45,
                "visible": options.show_axes,
            },
            angularaxis={
                "direction": (
                    "counterclockwise"
                    if int(getattr(panel, "theta_direction", 1)) >= 0
                    else "clockwise"
                ),
                "rotation": _polar_rotation(getattr(panel, "theta_zero_location", "N")),
                "tickmode": "array",
                "tickvals": [0.0, 90.0, 180.0, 270.0],
                "ticktext": _polar_direction_ticktext(panel, options.axis_label_mode),
                "showgrid": bool(getattr(panel, "grid", True)) and options.show_grid,
                "gridcolor": palette["grid"],
                "gridwidth": 1,
                "showline": options.show_axes,
                "linecolor": palette["axis"],
                "linewidth": 1.2,
                "tickfont": {"color": palette["text_soft"], "size": 10},
                "visible": options.show_axes,
            },
            bgcolor=palette["transparent"],
        )

    figure = apply_layout(
        figure,
        title=scientific_math_label(spec.title),
        options=_merge_options(options, show_legend=bool(getattr(spec, "show_legend", True))),
    )
    figure.update_layout(
        height=max(640, 540 * rows),
        margin={"l": 48, "r": 48, "t": 92, "b": 100},
        legend={
            "orientation": "h",
            "x": 0.5,
            "xanchor": "center",
            "y": -0.08,
            "yanchor": "top",
            "bgcolor": palette["transparent"],
            "borderwidth": 0,
        },
    )
    figure.update_annotations(font={"color": palette["text"], "size": 14})
    return figure


def _surface_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    figure = go.Figure()
    for index, layer in enumerate(getattr(spec, "layers", ())):
        style = layer.style
        lower, upper = limits(getattr(style, "value_limits", None))
        requested_colormap = options.colormap or getattr(style, "colormap", None)
        color = getattr(style, "color", None)
        surface_kwargs: dict[str, Any] = {
            "x": array(layer.x),
            "y": array(layer.y),
            "z": array(layer.z),
            "name": scientific_math_label(layer.label),
            "opacity": (
                float(getattr(style, "opacity", 1.0))
                if options.surface_opacity is None
                else options.surface_opacity
            ),
            "showscale": bool(getattr(style, "show_colorbar", True)) and options.show_colorbar,
            "cmin": lower,
            "cmax": upper,
            "colorbar": colorbar_options(spec.value_axis, x=0.90),
            "customdata": array(layer.values),
            "hovertemplate": (
                "x: %{x:.6g}<br>y: %{y:.6g}<br>z: %{z:.6g}<br>"
                f"{axis_title(spec.value_axis)}: %{{customdata:.6g}}<extra></extra>"
            ),
        }
        if requested_colormap:
            surface_kwargs.update(
                surfacecolor=array(layer.values),
                colorscale=colorscale(requested_colormap),
            )
        else:
            resolved_color = series_color(index, color)
            surface_kwargs.update(
                surfacecolor=np.zeros_like(array(layer.values), dtype=float),
                colorscale=[[0.0, resolved_color], [1.0, resolved_color]],
                showscale=False,
            )
        figure.add_trace(go.Surface(**surface_kwargs))

    if options.show_polarizations:
        maximum_extent = _surface_maximum_extent(spec)
        for vector_index, vector_layer in enumerate(getattr(spec, "vector_layers", ())):
            _add_vector_layer(
                figure,
                vector_layer,
                index=vector_index,
                options=options,
                maximum_extent=maximum_extent,
            )

    figure = apply_layout(
        figure,
        title=scientific_math_label(spec.title),
        options=options,
        three_dimensional=True,
    )
    _configure_surface_axes(figure, spec, options)
    if bool(getattr(spec, "equal_aspect", True)):
        figure.update_layout(scene_aspectmode="data")
    if options.show_colorbar:
        figure.update_layout(margin={"l": 54, "r": 142, "t": 76, "b": 54})
    return figure


def _spherical_map(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    """Render smooth projected hemispheres equivalent to Quantas contour maps."""
    projection = (
        getattr(spec, "projection", "equal_area")
        if options.projection == "source"
        else options.projection
    )
    panels = _spherical_panels(spec)
    figure = make_subplots(
        rows=1,
        cols=len(panels),
        subplot_titles=[
            f"{hemisphere.capitalize()} hemisphere" if len(panels) > 1 else ""
            for hemisphere, _theta, _values in panels
        ],
        horizontal_spacing=0.08,
    )
    for index, (hemisphere, theta, values) in enumerate(panels):
        _add_spherical_panel(
            figure,
            spec,
            hemisphere=hemisphere,
            theta=theta,
            values=values,
            projection=str(projection),
            options=options,
            row=1,
            column=index + 1,
            axis_index=index + 1,
            show_colorbar=index == len(panels) - 1 and options.show_colorbar,
            compact=False,
        )
    palette = theme_palette(options)
    figure = apply_layout(figure, title=scientific_math_label(spec.title), options=options)
    figure.update_layout(
        height=700,
        margin={"l": 42, "r": 42, "t": 88, "b": 118},
    )
    figure.update_annotations(font={"color": palette["text"], "size": 14})
    return figure


def _spherical_summary(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    """Render a compact contour-map summary using the same scientific geometry."""
    maps = list(getattr(spec, "maps", ()))
    if not maps:
        raise ValueError("a spherical summary requires at least one map")
    rows, columns = subplot_grid(len(maps), int(getattr(spec, "columns", 3)))
    figure = make_subplots(
        rows=rows,
        cols=columns,
        subplot_titles=[scientific_math_label(item.title) for item in maps],
        horizontal_spacing=0.07,
        vertical_spacing=0.14,
    )
    for index, map_spec in enumerate(maps):
        row = index // columns + 1
        column = index % columns + 1
        panels = _spherical_panels(map_spec)
        hemisphere, theta, values = next(
            (panel for panel in panels if panel[0] == "upper"),
            panels[0],
        )
        projection = (
            getattr(map_spec, "projection", "equal_area")
            if options.projection == "source"
            else options.projection
        )
        _add_spherical_panel(
            figure,
            map_spec,
            hemisphere=hemisphere,
            theta=theta,
            values=values,
            projection=str(projection),
            options=options,
            row=row,
            column=column,
            axis_index=index + 1,
            show_colorbar=index == len(maps) - 1 and options.show_colorbar,
            compact=True,
        )
    palette = theme_palette(options)
    figure = apply_layout(figure, title=scientific_math_label(spec.title), options=options)
    figure.update_layout(
        height=max(620, 500 * rows),
        margin={"l": 36, "r": 36, "t": 88, "b": 112},
    )
    figure.update_annotations(font={"color": palette["text"], "size": 13})
    return figure


def _add_spherical_panel(
    figure: go.Figure,
    spec: Any,
    *,
    hemisphere: str,
    theta: np.ndarray,
    values: np.ndarray,
    projection: str,
    options: PlotlyRenderOptions,
    row: int,
    column: int,
    axis_index: int,
    show_colorbar: bool,
    compact: bool,
) -> None:
    grid, mapped = _projected_scalar_grid(
        theta,
        array(spec.phi),
        values,
        hemisphere=hemisphere,
        projection=projection,
        resolution=141 if compact else 181,
    )
    finite = mapped[np.isfinite(mapped)]
    if finite.size == 0:
        raise ValueError(f"spherical map {getattr(spec, 'key', '')!r} contains no finite values")
    lower, upper = limits(getattr(spec.value_axis, "limits", None))
    selected_colormap = options.colormap or getattr(spec, "colormap", "viridis")
    show_lines = (
        bool(getattr(spec, "isolines", True))
        if options.show_isolines is None
        else options.show_isolines
    )
    show_labels = bool(options.show_isoline_labels)
    source_levels = int(getattr(spec, "levels", 12))
    filled = go.Contour(
        x=grid,
        y=grid,
        z=mapped,
        colorscale=colorscale(selected_colormap),
        zmin=lower,
        zmax=upper,
        ncontours=max(24, source_levels * 3),
        contours={"coloring": "heatmap", "showlines": False},
        connectgaps=False,
        showscale=show_colorbar,
        colorbar=colorbar_options(
            spec.value_axis,
            compact=compact,
            horizontal=True,
            y=-0.15 if compact else -0.13,
        ),
        customdata=mapped,
        name=str(spec.title),
        hovertemplate=(
            "map x: %{x:.5g}<br>map y: %{y:.5g}<br>"
            f"{axis_title(spec.value_axis)}: %{{z:.7g}}<extra></extra>"
        ),
    )
    center = getattr(spec, "metadata", {}).get("color_center")
    if center is not None:
        filled.update(zmid=float(center))
    figure.add_trace(filled, row=row, col=column)

    if show_lines:
        palette = theme_palette(options)
        level_count = options.contour_levels or source_levels
        contour_levels = _exact_contour_levels(
            mapped,
            count=level_count,
            lower=lower,
            upper=upper,
        )
        isolines = go.Contour(
            x=grid,
            y=grid,
            z=mapped,
            zmin=lower,
            zmax=upper,
            autocontour=contour_levels["autocontour"],
            ncontours=level_count,
            contours={
                "coloring": "none",
                "showlines": True,
                "showlabels": show_labels,
                **contour_levels["contours"],
            },
            line={
                "color": portable_color(options.line_color, palette["axis"]),
                "width": options.line_width or (0.55 if compact else 0.75),
            },
            connectgaps=False,
            showscale=False,
            hoverinfo="skip",
            name=f"{spec.title} isolines",
            showlegend=False,
        )
        figure.add_trace(isolines, row=row, col=column)

    _add_spherical_markers(
        figure,
        spec,
        hemisphere=hemisphere,
        projection=projection,
        row=row,
        column=column,
        compact=compact,
    )
    if options.show_polarizations:
        _add_axis_fields(
            figure,
            spec,
            hemisphere=hemisphere,
            projection=projection,
            options=options,
            row=row,
            column=column,
            compact=compact,
        )
    _decorate_spherical_subplot(
        figure,
        hemisphere=hemisphere,
        options=options,
        row=row,
        column=column,
        axis_index=axis_index,
        compact=compact,
    )


def _spherical_panels(spec: Any) -> list[tuple[str, FloatArray, FloatArray]]:
    """Split a full-sphere specification into upper and lower hemispheres."""
    theta: FloatArray = np.asarray(spec.theta, dtype=float)
    values: FloatArray = np.asarray(spec.values, dtype=float)
    hemisphere = str(getattr(spec, "hemisphere", "upper"))
    if hemisphere == "upper":
        return [("upper", theta, values)]
    if hemisphere == "lower":
        return [("lower", theta, values)]
    tolerance = 16.0 * np.finfo(float).eps
    upper = theta <= 0.5 * np.pi + tolerance
    lower = theta >= 0.5 * np.pi - tolerance
    return [("upper", theta[upper], values[upper]), ("lower", theta[lower], values[lower])]


def _projected_scalar_grid(
    theta: FloatArray,
    phi: FloatArray,
    values: FloatArray,
    *,
    hemisphere: str,
    projection: str,
    resolution: int,
) -> tuple[FloatArray, FloatArray]:
    """Interpolate a regular angular field onto a projected unit-disk grid."""
    theta_values: FloatArray = np.asarray(theta, dtype=float)
    phi_values: FloatArray = np.asarray(phi, dtype=float)
    mapped_values: FloatArray = np.asarray(values, dtype=float)
    if mapped_values.shape != (theta_values.size, phi_values.size):
        raise ValueError("spherical values must have shape (len(theta), len(phi))")
    phi_closed: FloatArray = np.concatenate((phi_values, [2.0 * np.pi]))
    values_closed: FloatArray = np.concatenate((mapped_values, mapped_values[:, :1]), axis=1)
    theta_grid: FloatArray
    phi_grid: FloatArray
    theta_grid, phi_grid = np.meshgrid(theta_values, phi_closed, indexing="ij")
    x: FloatArray
    y: FloatArray
    x, y = _project_angles(
        theta_grid,
        phi_grid,
        hemisphere=hemisphere,
        projection=projection,
    )
    finite: BoolArray = np.isfinite(values_closed) & np.isfinite(x) & np.isfinite(y)
    if not np.any(finite):
        raise ValueError("spherical map contains no finite projected samples")
    points: FloatArray = np.column_stack((x[finite], y[finite]))
    samples: FloatArray = values_closed[finite]
    grid: FloatArray = np.linspace(-1.0, 1.0, max(81, int(resolution)))
    grid_x: FloatArray
    grid_y: FloatArray
    grid_x, grid_y = np.meshgrid(grid, grid, indexing="xy")
    try:
        from scipy.interpolate import griddata

        interpolated: FloatArray = np.asarray(
            griddata(points, samples, (grid_x, grid_y), method="linear"),
            dtype=float,
        )
        missing: BoolArray = np.isnan(interpolated) & (grid_x**2 + grid_y**2 <= 1.0 + 1.0e-12)
        if np.any(missing):
            nearest: FloatArray = np.asarray(
                griddata(points, samples, (grid_x, grid_y), method="nearest"),
                dtype=float,
            )
            interpolated[missing] = nearest[missing]
    except ImportError:  # pragma: no cover - Quantas installs SciPy
        interpolated = _nearest_projected_grid(points, samples, grid_x, grid_y)
    interpolated[grid_x**2 + grid_y**2 > 1.0 + 1.0e-12] = np.nan
    return grid, np.asarray(interpolated, dtype=float)


def _nearest_projected_grid(
    points: FloatArray,
    samples: FloatArray,
    grid_x: FloatArray,
    grid_y: FloatArray,
) -> FloatArray:
    """Provide a bounded NumPy fallback when SciPy is unavailable."""
    targets: FloatArray = np.column_stack((grid_x.ravel(), grid_y.ravel()))
    result: FloatArray = np.empty(targets.shape[0], dtype=float)
    chunk_size = 512
    for start in range(0, targets.shape[0], chunk_size):
        chunk: FloatArray = targets[start : start + chunk_size]
        distances: FloatArray = np.sum((chunk[:, None, :] - points[None, :, :]) ** 2, axis=2)
        result[start : start + chunk.shape[0]] = samples[np.argmin(distances, axis=1)]
    return result.reshape(grid_x.shape)


def _decorate_spherical_subplot(
    figure: go.Figure,
    *,
    hemisphere: str,
    options: PlotlyRenderOptions,
    row: int,
    column: int,
    axis_index: int,
    compact: bool,
) -> None:
    """Draw the projection boundary and tensor-frame direction labels."""
    palette = theme_palette(options)
    line_width = 1.0 if compact else 1.3
    figure.add_shape(
        type="circle",
        x0=-1.0,
        y0=-1.0,
        x1=1.0,
        y1=1.0,
        line={"color": palette["axis"], "width": line_width},
        fillcolor="rgba(0,0,0,0)",
        row=row,
        col=column,
    )
    for x0, y0, x1, y1 in ((-1.0, 0.0, 1.0, 0.0), (0.0, -1.0, 0.0, 1.0)):
        figure.add_shape(
            type="line",
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            line={"color": palette["axis"], "width": 0.7},
            row=row,
            col=column,
        )
    font_size = 9 if compact else 11
    if options.axis_label_mode == "crystal":
        direction_labels = (
            "[100]",
            "[−100]",
            "[010]",
            "[0−10]",
            "[001]" if hemisphere == "upper" else "[00−1]",
        )
    else:
        direction_labels = (
            "+x",
            "−x",
            "+y",
            "−y",
            "+z" if hemisphere == "upper" else "−z",
        )
    labels = (
        (1.055, 0.0, direction_labels[0], "left", "middle"),
        (-1.055, 0.0, direction_labels[1], "right", "middle"),
        (0.0, 1.055, direction_labels[2], "center", "bottom"),
        (0.0, -1.055, direction_labels[3], "center", "top"),
        (0.0, -0.045, direction_labels[4], "center", "top"),
    )
    for x, y, text, xanchor, yanchor in labels:
        figure.add_annotation(
            x=x,
            y=y,
            text=text,
            showarrow=False,
            xanchor=xanchor,
            yanchor=yanchor,
            font={"color": palette["text"], "size": font_size},
            bgcolor=(palette["legend"] if x == 0.0 and abs(y) < 0.1 else None),
            borderpad=2,
            row=row,
            col=column,
        )
    x_reference = "x" if axis_index == 1 else f"x{axis_index}"
    figure.update_xaxes(
        range=[-1.12, 1.12],
        visible=False,
        constrain="domain",
        row=row,
        col=column,
    )
    figure.update_yaxes(
        range=[-1.12, 1.12],
        visible=False,
        scaleanchor=x_reference,
        scaleratio=1,
        row=row,
        col=column,
    )


def _panel_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    """Render one public panel collection with non-overlapping colorbars."""
    panels = list(getattr(spec, "panels", ()))
    rows, columns = subplot_grid(len(panels), int(getattr(spec, "columns", 2)))
    figure = make_subplots(
        rows=rows,
        cols=columns,
        subplot_titles=[scientific_math_label(panel.title) for panel in panels],
        shared_xaxes=bool(getattr(spec, "share_x", False)),
        shared_yaxes=bool(getattr(spec, "share_y", False)),
        horizontal_spacing=0.10,
        vertical_spacing=0.14,
    )
    shared_marker_colorbars: set[tuple[str, str, str, str]] = set()
    has_vertical_colorbar = False
    for index, panel in enumerate(panels):
        row = index // columns + 1
        column = index % columns + 1
        child = render_plot(panel, options=options)
        for source_trace in child.data:
            trace = go.Figure(data=[source_trace]).data[0]
            marker = getattr(trace, "marker", None)
            if marker is not None and bool(getattr(marker, "showscale", False)):
                colorbar = getattr(marker, "colorbar", None)
                title = ""
                if colorbar is not None and getattr(colorbar, "title", None) is not None:
                    title = str(getattr(colorbar.title, "text", ""))
                key = (
                    title or "marker-scale",
                    repr(getattr(marker, "colorscale", None)),
                    repr(getattr(marker, "cmin", None)),
                    repr(getattr(marker, "cmax", None)),
                )
                if key in shared_marker_colorbars:
                    marker.showscale = False
                else:
                    shared_marker_colorbars.add(key)
                    marker.colorbar.update(
                        x=1.005,
                        y=0.5,
                        len=0.72,
                        thickness=14,
                        xanchor="left",
                        yanchor="middle",
                    )
                    has_vertical_colorbar = True
            if bool(getattr(trace, "showscale", False)) and hasattr(trace, "colorbar"):
                xaxis_name = "xaxis" if index == 0 else f"xaxis{index + 1}"
                yaxis_name = "yaxis" if index == 0 else f"yaxis{index + 1}"
                x_domain = getattr(figure.layout, xaxis_name).domain
                y_domain = getattr(figure.layout, yaxis_name).domain
                trace.colorbar.update(
                    x=min(float(x_domain[1]) + 0.012, 1.005),
                    y=0.5 * (float(y_domain[0]) + float(y_domain[1])),
                    len=max(0.18, 0.72 * (float(y_domain[1]) - float(y_domain[0]))),
                    thickness=11,
                    xanchor="left",
                    yanchor="middle",
                )
                has_vertical_colorbar = True
            figure.add_trace(trace, row=row, col=column)
        if hasattr(panel, "x_axis"):
            figure.update_xaxes(title_text=axis_title(panel.x_axis), row=row, col=column)
        if hasattr(panel, "y_axis"):
            figure.update_yaxes(title_text=axis_title(panel.y_axis), row=row, col=column)
        if bool(getattr(panel, "invert_x_axis", False)):
            figure.update_xaxes(autorange="reversed", row=row, col=column)
        if bool(getattr(panel, "invert_y_axis", False)):
            figure.update_yaxes(autorange="reversed", row=row, col=column)
    figure = apply_layout(
        figure,
        title=scientific_math_label(spec.title),
        options=options,
    )
    figure.update_layout(
        height=max(520, rows * 440),
        legend={
            "orientation": "h",
            "x": 0.5,
            "xanchor": "center",
            "y": -0.08,
            "yanchor": "top",
        },
        margin={
            "l": 82,
            "r": 142 if has_vertical_colorbar else 72,
            "t": 88,
            "b": 112,
        },
    )
    return figure


def _add_scalar_background(
    figure: go.Figure,
    background: Any,
    *,
    override_colormap: str | None,
) -> None:
    """Approximate one-dimensional scalar backgrounds with bounded spans."""
    coordinates: NDArray[np.float64] = array(background.coordinates).astype(float).ravel()
    values: NDArray[np.float64] = array(background.values).astype(float).ravel()
    if coordinates.size < 2 or coordinates.size != values.size:
        return
    maximum_spans = 160
    step = max(1, int(np.ceil((coordinates.size - 1) / maximum_spans)))
    sampled_indices = list(range(0, coordinates.size - 1, step))
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return
    lower, upper = limits(getattr(background, "value_limits", None))
    value_min = float(np.min(finite)) if lower is None else lower
    value_max = float(np.max(finite)) if upper is None else upper
    scale = override_colormap or getattr(background, "colormap", "viridis")
    denominator = value_max - value_min
    for index in sampled_indices:
        end = min(index + step, coordinates.size - 1)
        value = float(np.nanmean(values[index : end + 1]))
        fraction = 0.5 if denominator == 0.0 else (value - value_min) / denominator
        color = sample_colorscale(colorscale(scale), [max(0.0, min(1.0, fraction))])[0]
        arguments = {
            "fillcolor": color,
            "opacity": float(getattr(background, "alpha", 0.2)),
            "line_width": 0,
            "layer": "below",
        }
        if getattr(background, "axis", "y") == "x":
            figure.add_vrect(x0=coordinates[index], x1=coordinates[end], **arguments)
        else:
            figure.add_hrect(y0=coordinates[index], y1=coordinates[end], **arguments)


def _add_secondary_axes(figure: go.Figure, axes: Any) -> None:
    """Add portable labelled tick axes on the top or right of a line plot."""
    x_count = 0
    y_count = 0
    for secondary in axes:
        orientation = str(getattr(secondary, "orientation", "x"))
        location = str(getattr(secondary, "location", "top"))
        positions = array(secondary.positions).tolist()
        labels = [str(item) for item in secondary.labels]
        if orientation == "y":
            y_count += 1
            axis_name = f"yaxis{y_count + 1}"
            figure.update_layout(
                **{
                    axis_name: {
                        "title": scientific_math_label(secondary.label),
                        "overlaying": "y",
                        "side": "right" if location == "right" else "left",
                        "tickmode": "array",
                        "tickvals": positions,
                        "ticktext": labels,
                        "showgrid": False,
                    }
                }
            )
        else:
            x_count += 1
            axis_name = f"xaxis{x_count + 1}"
            figure.update_layout(
                **{
                    axis_name: {
                        "title": scientific_math_label(secondary.label),
                        "overlaying": "x",
                        "side": "bottom" if location == "bottom" else "top",
                        "tickmode": "array",
                        "tickvals": positions,
                        "ticktext": labels,
                        "showgrid": False,
                    }
                }
            )


def _add_cartesian_series(
    figure: go.Figure,
    series: Any,
    *,
    index: int,
    marker: str | None,
    options: PlotlyRenderOptions,
) -> None:
    style = series.style
    mode = "lines+markers" if marker is not None else "lines"
    color = series_color(index, options.line_color or getattr(style, "color", None))
    figure.add_trace(
        go.Scattergl(
            x=array(series.x),
            y=array(series.y),
            mode=mode,
            name=scientific_math_label(series.label),
            opacity=float(getattr(style, "alpha", 1.0)),
            line={
                "color": color,
                "width": options.line_width or float(getattr(style, "line_width", 1.5)),
                "dash": line_dash(getattr(style, "line_style", "solid")),
            },
            marker={
                "symbol": marker,
                "size": float(getattr(style, "marker_size", 6.0) or 6.0),
                "color": color,
                "line": {
                    "color": portable_color(getattr(style, "marker_edge_color", None), "#04101a"),
                    "width": float(getattr(style, "marker_edge_width", 0.0) or 0.0),
                },
            },
            error_x=None
            if getattr(series, "x_error", None) is None
            else {
                "type": "data",
                "array": array(series.x_error),
                "visible": True,
                "thickness": float(getattr(style, "errorbar_line_width", 1.0)),
            },
            error_y=None
            if getattr(series, "y_error", None) is None
            else {
                "type": "data",
                "array": array(series.y_error),
                "visible": True,
                "thickness": float(getattr(style, "errorbar_line_width", 1.0)),
            },
            hovertemplate="x: %{x:.8g}<br>y: %{y:.8g}<extra>%{fullData.name}</extra>",
        )
    )


def _add_colored_path(
    figure: go.Figure,
    path: Any,
    *,
    index: int,
    marker: str,
    override_colormap: str | None,
    options: PlotlyRenderOptions,
) -> None:
    style = path.style
    lower, upper = limits(getattr(style, "value_limits", None))
    selected = override_colormap or getattr(style, "colormap", "viridis")
    figure.add_trace(
        go.Scattergl(
            x=array(path.x),
            y=array(path.y),
            mode="lines+markers",
            name=scientific_math_label(path.label),
            line={
                "color": series_color(index, options.line_color),
                "width": options.line_width or float(getattr(style, "line_width", 1.8)),
                "dash": line_dash(getattr(style, "line_style", "solid")),
            },
            marker={
                "symbol": marker,
                "color": array(path.values),
                "colorscale": colorscale(selected),
                "cmin": lower,
                "cmax": upper,
                "showscale": bool(getattr(style, "show_colorbar", True)) and options.show_colorbar,
                "colorbar": colorbar_options(path.value_axis),
                "size": float(getattr(style, "marker_size", 5.0) or 5.0),
            },
            customdata=array(path.values),
            hovertemplate=(
                "x: %{x:.8g}<br>y: %{y:.8g}<br>"
                f"{axis_title(path.value_axis)}: %{{customdata:.8g}}<extra></extra>"
            ),
        )
    )


def _add_vector_layer(
    figure: go.Figure,
    layer: Any,
    *,
    index: int,
    options: PlotlyRenderOptions,
    maximum_extent: float,
) -> None:
    """Render one public Cartesian polarization layer like Quantas Matplotlib."""
    origins = array(layer.origins)
    vectors = array(layer.vectors)
    style = layer.style
    resolved = getattr(layer, "resolved_mask", None)
    mask = np.all(np.isfinite(origins), axis=1) & np.all(np.isfinite(vectors), axis=1)
    if resolved is not None:
        mask &= array(resolved).astype(bool)
    origins = origins[mask]
    vectors = vectors[mask]
    stride = max(1, options.polarization_stride)
    origins = origins[::stride]
    vectors = vectors[::stride]
    if origins.size == 0:
        return

    norms = np.linalg.norm(vectors, axis=1)
    usable = np.isfinite(norms) & (norms > 0.0)
    origins = origins[usable]
    vectors = vectors[usable] / norms[usable, None]
    if origins.size == 0:
        return

    palette = theme_palette(options)
    source_color = getattr(style, "color", None)
    color = options.polarization_color or _theme_safe_polarization_color(
        source_color,
        palette=palette,
        index=index,
    )
    scale_fraction = (
        options.polarization_scale
        if options.polarization_scale is not None
        else float(getattr(style, "scale", 0.08))
    )
    length = max(scale_fraction * maximum_extent, 1.0e-12)
    line_width = options.polarization_line_width or float(getattr(style, "line_width", 1.0))
    opacity = float(getattr(style, "opacity", 1.0))

    if bool(getattr(layer, "axial", False)):
        half = 0.5 * length * vectors
        starts = origins - half
        ends = origins + half
        x: list[float | None] = []
        y: list[float | None] = []
        z: list[float | None] = []
        for start, end in zip(starts, ends, strict=True):
            x.extend([float(start[0]), float(end[0]), None])
            y.extend([float(start[1]), float(end[1]), None])
            z.extend([float(start[2]), float(end[2]), None])
        figure.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line={"color": color, "width": line_width},
                opacity=opacity,
                name=str(layer.label),
                hoverinfo="skip",
            )
        )
        return

    scaled = vectors * length
    figure.add_trace(
        go.Cone(
            x=origins[:, 0],
            y=origins[:, 1],
            z=origins[:, 2],
            u=scaled[:, 0],
            v=scaled[:, 1],
            w=scaled[:, 2],
            colorscale=[[0.0, color], [1.0, color]],
            showscale=False,
            sizemode="absolute",
            sizeref=length,
            opacity=opacity,
            name=str(layer.label),
        )
    )


def _configure_surface_axes(
    figure: go.Figure,
    spec: Any,
    options: PlotlyRenderOptions,
) -> None:
    """Draw origin-centred 3D axes following the Quantas Matplotlib renderer."""
    figure.update_layout(
        scene={
            "xaxis": {"visible": False, "showbackground": False},
            "yaxis": {"visible": False, "showbackground": False},
            "zaxis": {"visible": False, "showbackground": False},
        }
    )
    if not options.show_axes or not bool(getattr(spec, "show_axes", True)):
        return

    finite_coordinates: list[FloatArray] = []
    for layer in getattr(spec, "layers", ()):
        for coordinate in (layer.x, layer.y, layer.z):
            values = np.asarray(coordinate, dtype=float).ravel()
            finite_coordinates.append(values[np.isfinite(values)])
    finite_coordinates = [item for item in finite_coordinates if item.size]
    extent = (
        max(float(np.max(np.abs(item))) for item in finite_coordinates)
        if finite_coordinates
        else 1.0
    )
    extent = max(extent, 1.0e-12) * 1.08
    palette = theme_palette(options)
    labels = (
        ("[100]", "[010]", "[001]") if options.axis_label_mode == "crystal" else ("x", "y", "z")
    )
    coordinates = (
        ([-extent, extent], [0.0, 0.0], [0.0, 0.0]),
        ([0.0, 0.0], [-extent, extent], [0.0, 0.0]),
        ([0.0, 0.0], [0.0, 0.0], [-extent, extent]),
    )
    for index, ((x, y, z), label) in enumerate(zip(coordinates, labels, strict=True)):
        figure.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines+text",
                line={"color": palette["axis"], "width": 5},
                text=["", label],
                textposition="top center",
                textfont={"color": palette["text"], "size": 13},
                name=f"{label} axis",
                showlegend=False,
                hoverinfo="skip",
                legendrank=1000 + index,
            )
        )


def _add_spherical_markers(
    figure: go.Figure,
    spec: Any,
    *,
    hemisphere: str,
    projection: str,
    row: int,
    column: int,
    compact: bool,
) -> None:
    """Render extrema markers using the same minimum/maximum convention as Matplotlib."""
    for marker in getattr(spec, "markers", ()):
        x, y, _eligible = _project_directions(
            array(marker.directions),
            hemisphere=hemisphere,
            projection=projection,
            antipodal=bool(getattr(marker, "metadata", {}).get("antipodal", False)),
        )
        if x.size == 0:
            continue
        is_minimum = str(getattr(marker, "key", "")) == "minimum"
        value = getattr(marker, "metadata", {}).get("value")
        value_text = "" if not isinstance(value, (float, int)) else f"<br>{float(value):.6g}"
        figure.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker={
                    "symbol": marker_symbol(getattr(marker, "marker", "circle")),
                    "size": 8 if compact else 11,
                    "color": "white" if is_minimum else "black",
                    "line": {
                        "color": "black" if is_minimum else "white",
                        "width": 1.2,
                    },
                },
                name=str(marker.label),
                showlegend=False,
                hovertemplate=(
                    f"{marker.label}{value_text}<br>map x: %{{x:.5g}}<br>"
                    "map y: %{y:.5g}<extra></extra>"
                ),
            ),
            row=row,
            col=column,
        )


def _add_axis_fields(
    figure: go.Figure,
    spec: Any,
    *,
    hemisphere: str,
    projection: str,
    options: PlotlyRenderOptions,
    row: int,
    column: int,
    compact: bool,
) -> None:
    """Render projected axial fields such as shear-wave polarizations."""
    palette = theme_palette(options)
    for layer in getattr(spec, "axis_layers", ()):
        directions: FloatArray = np.asarray(layer.directions, dtype=float)
        axes: FloatArray = np.asarray(layer.axes, dtype=float)
        mask: BoolArray = np.all(np.isfinite(directions), axis=1) & np.all(
            np.isfinite(axes), axis=1
        )
        if getattr(layer, "resolved_mask", None) is not None:
            mask &= np.asarray(layer.resolved_mask, dtype=bool)
        directions = directions[mask]
        axes = axes[mask]
        stride = max(1, options.polarization_stride)
        directions = directions[::stride]
        axes = axes[::stride]
        segments_x: list[float | None] = []
        segments_y: list[float | None] = []
        length = options.polarization_scale or (0.045 if compact else 0.065)
        for direction, polarization in zip(directions, axes, strict=True):
            prepared_direction: FloatArray = direction.copy()
            flip_to_hemisphere = (hemisphere == "upper" and prepared_direction[2] < 0.0) or (
                hemisphere == "lower" and prepared_direction[2] > 0.0
            )
            if flip_to_hemisphere:
                prepared_direction *= -1.0
            if hemisphere == "upper" and prepared_direction[2] < -1.0e-12:
                continue
            if hemisphere == "lower" and prepared_direction[2] > 1.0e-12:
                continue
            tangent: FloatArray = (
                polarization - np.dot(polarization, prepared_direction) * prepared_direction
            )
            norm = float(np.linalg.norm(tangent))
            if not np.isfinite(norm) or norm <= 1.0e-10:
                continue
            tangent /= norm
            epsilon = 1.0e-4
            plus: FloatArray = prepared_direction + epsilon * tangent
            minus: FloatArray = prepared_direction - epsilon * tangent
            plus /= np.linalg.norm(plus)
            minus /= np.linalg.norm(minus)
            px: FloatArray
            py: FloatArray
            px, py, _ = _project_directions(
                np.stack((plus, minus)),
                hemisphere=hemisphere,
                projection=projection,
                antipodal=False,
            )
            cx: FloatArray
            cy: FloatArray
            cx, cy, _ = _project_directions(
                prepared_direction[None, :],
                hemisphere=hemisphere,
                projection=projection,
                antipodal=False,
            )
            if px.size != 2 or cx.size != 1:
                continue
            direction_2d: FloatArray = np.array([px[0] - px[1], py[0] - py[1]])
            direction_norm = float(np.linalg.norm(direction_2d))
            if direction_norm <= 1.0e-12:
                continue
            direction_2d /= direction_norm
            center: FloatArray = np.array([cx[0], cy[0]])
            half: FloatArray = 0.5 * length * direction_2d
            start: FloatArray = center - half
            end: FloatArray = center + half
            segments_x.extend([float(start[0]), float(end[0]), None])
            segments_y.extend([float(start[1]), float(end[1]), None])
        if not segments_x:
            continue
        figure.add_trace(
            go.Scatter(
                x=segments_x,
                y=segments_y,
                mode="lines",
                line={
                    "color": options.polarization_color or palette["text"],
                    "width": options.polarization_line_width or (1.0 if compact else 1.4),
                },
                opacity=0.9,
                name=str(layer.label),
                showlegend=not compact,
                hoverinfo="skip",
            ),
            row=row,
            col=column,
        )


def _project_angles(
    theta: FloatArray,
    phi: FloatArray,
    *,
    hemisphere: str,
    projection: str,
) -> tuple[FloatArray, FloatArray]:
    """Project spherical angles with the same orientation used by Quantas Matplotlib."""
    alpha: FloatArray = np.asarray(theta, dtype=float)
    if hemisphere == "lower":
        alpha = pi - alpha
    if projection == "stereographic":
        radius: FloatArray = np.tan(alpha / 2.0)
    else:
        radius = np.sqrt(2.0) * np.sin(alpha / 2.0)
    return radius * np.cos(phi), radius * np.sin(phi)


def _project_directions(
    directions: FloatArray,
    *,
    hemisphere: str,
    projection: str,
    antipodal: bool,
) -> tuple[FloatArray, FloatArray, BoolArray]:
    """Project Cartesian directions into one selected hemisphere."""
    vectors: FloatArray = np.asarray(directions, dtype=float).copy()
    if antipodal:
        wrong: BoolArray = vectors[:, 2] < 0.0 if hemisphere == "upper" else vectors[:, 2] > 0.0
        vectors[wrong] *= -1.0
    eligible: BoolArray = (
        vectors[:, 2] >= -1.0e-12 if hemisphere == "upper" else vectors[:, 2] <= 1.0e-12
    )
    norms: FloatArray = np.linalg.norm(vectors, axis=1)
    eligible &= np.isfinite(norms) & (norms > 0.0)
    unit: FloatArray = vectors[eligible] / norms[eligible, None]
    theta: FloatArray = np.arccos(np.clip(unit[:, 2], -1.0, 1.0))
    phi: FloatArray = np.mod(np.arctan2(unit[:, 1], unit[:, 0]), 2.0 * np.pi)
    x: FloatArray
    y: FloatArray
    x, y = _project_angles(
        theta,
        phi,
        hemisphere=hemisphere,
        projection=projection,
    )
    return x, y, eligible


def _exact_contour_levels(
    values: FloatArray,
    *,
    count: int,
    lower: float | None,
    upper: float | None,
) -> dict[str, Any]:
    """Return deterministic Plotly contour levels with exactly ``count`` values."""
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0 or count < 2:
        return {"autocontour": True, "contours": {}}
    minimum = float(np.min(finite)) if lower is None else float(lower)
    maximum = float(np.max(finite)) if upper is None else float(upper)
    if not np.isfinite(minimum) or not np.isfinite(maximum) or maximum <= minimum:
        return {"autocontour": True, "contours": {}}
    return {
        "autocontour": False,
        "contours": {
            "start": minimum,
            "end": maximum,
            "size": (maximum - minimum) / float(count - 1),
        },
    }


def _surface_maximum_extent(spec: Any) -> float:
    """Return the maximum finite Cartesian extent of public surface layers."""
    maximum = 0.0
    for layer in getattr(spec, "layers", ()):
        for coordinate in (layer.x, layer.y, layer.z):
            values = np.asarray(coordinate, dtype=float)
            finite = values[np.isfinite(values)]
            if finite.size:
                maximum = max(maximum, float(np.max(np.abs(finite))))
    return max(maximum, 1.0e-12)


def _theme_safe_polarization_color(
    color: Any,
    *,
    palette: dict[str, str],
    index: int,
) -> str:
    """Keep backend polarization styles visible on both GUI themes."""
    normalized = str(color or "").strip().lower()
    if normalized in {"", "none"}:
        return palette["text"]
    dark = palette["text"].lower() == "#ecf5fb"
    if normalized in {"black", "#000", "#000000", "#111", "#111111"} and dark:
        return palette["text"]
    if normalized in {"white", "#fff", "#ffffff", "#f7fafc"} and not dark:
        return palette["text"]
    return series_color(index, str(color))


def _apply_axis_limits(figure: go.Figure, axis_spec: Any, *, axis: str) -> None:
    lower, upper = limits(getattr(axis_spec, "limits", None))
    if lower is None and upper is None:
        return
    range_value = [lower, upper]
    if axis == "x":
        figure.update_xaxes(range=range_value)
    else:
        figure.update_yaxes(range=range_value)


def _polar_direction_ticktext(
    panel: Any,
    mode: str,
) -> list[str]:
    """Return principal-plane direction labels for one polar panel."""
    plane = str(getattr(panel, "metadata", {}).get("plane", getattr(panel, "key", "xy")))
    cartesian = {
        "xy": ["+x", "+y", "−x", "−y"],
        "xz": ["+z", "+x", "−z", "−x"],
        "yz": ["+z", "+y", "−z", "−y"],
    }
    crystal = {
        "xy": ["[100]", "[010]", "[−100]", "[0−10]"],
        "xz": ["[001]", "[100]", "[00−1]", "[−100]"],
        "yz": ["[001]", "[010]", "[00−1]", "[0−10]"],
    }
    labels = crystal if mode == "crystal" else cartesian
    return labels.get(plane.lower(), cartesian["xy"])


def _polar_rotation(location: str) -> float:
    return {"N": 90.0, "E": 0.0, "S": -90.0, "W": 180.0}.get(str(location).upper(), 90.0)


def _merge_options(options: PlotlyRenderOptions, *, show_legend: bool) -> PlotlyRenderOptions:
    return PlotlyRenderOptions(
        colormap=options.colormap,
        line_width=options.line_width,
        line_color=options.line_color,
        show_legend=options.show_legend and show_legend,
        show_grid=options.show_grid,
        show_axes=options.show_axes,
        axis_label_mode=options.axis_label_mode,
        show_colorbar=options.show_colorbar,
        show_isolines=options.show_isolines,
        show_isoline_labels=options.show_isoline_labels,
        contour_levels=options.contour_levels,
        surface_opacity=options.surface_opacity,
        show_polarizations=options.show_polarizations,
        polarization_stride=options.polarization_stride,
        polarization_line_width=options.polarization_line_width,
        polarization_scale=options.polarization_scale,
        polarization_color=options.polarization_color,
        hover_mode=options.hover_mode,
        projection=options.projection,
        camera=options.camera,
        template=options.template,
        uirevision=options.uirevision,
    )


def _control_profile(kind: str, spec: Any) -> PlotControlProfile:
    """Return controls meaningful for one public PlotSpec and its actual layers."""
    has_polarization = bool(getattr(spec, "axis_layers", ()) or getattr(spec, "vector_layers", ()))
    if kind == "SphericalSummarySpec":
        has_polarization = any(
            bool(getattr(item, "axis_layers", ())) for item in getattr(spec, "maps", ())
        )
    if kind == "ContourPlotSpec":
        return PlotControlProfile(
            colormap=True,
            contour=True,
            colorbar=True,
            line_style=True,
        )
    if kind == "SurfacePlotSpec":
        return PlotControlProfile(
            colormap=True,
            surface=True,
            colorbar=True,
            line_style=has_polarization,
            axis_labels=True,
            polarization=has_polarization,
            grid=False,
        )
    if kind in {"SphericalMapSpec", "SphericalSummarySpec"}:
        return PlotControlProfile(
            colormap=True,
            projection=True,
            contour=True,
            colorbar=True,
            line_style=True,
            axis_labels=True,
            polarization=has_polarization,
            grid=False,
        )
    if kind == "PolarPlotSpec":
        return PlotControlProfile(
            line_style=True,
            axis_labels=True,
            grid=True,
            axes=True,
        )
    if kind == "PanelPlotSpec":
        child_profiles: list[PlotControlProfile] = []
        for panel in getattr(spec, "panels", ()):
            child_kind = _typed_renderer(panel)[0]
            child_profiles.append(_control_profile(child_kind, panel))
        if not child_profiles:
            return PlotControlProfile()
        return PlotControlProfile(
            colormap=any(item.colormap for item in child_profiles),
            hover=any(item.hover for item in child_profiles),
            projection=any(item.projection for item in child_profiles),
            contour=any(item.contour for item in child_profiles),
            surface=any(item.surface for item in child_profiles),
            colorbar=any(item.colorbar for item in child_profiles),
            line_style=any(item.line_style for item in child_profiles),
            axis_labels=any(item.axis_labels for item in child_profiles),
            polarization=any(item.polarization for item in child_profiles),
            legend=any(item.legend for item in child_profiles),
            grid=any(item.grid for item in child_profiles),
            axes=any(item.axes for item in child_profiles),
        )
    return PlotControlProfile(line_style=kind == "LinePlotSpec")


def _rgba(color: str, alpha: float) -> str:
    if color.startswith("#") and len(color) == 7:
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        return f"rgba({red},{green},{blue},{alpha:.4g})"
    return color
