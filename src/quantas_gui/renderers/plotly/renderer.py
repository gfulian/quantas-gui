"""Plotly dispatcher for public Quantas ``PlotCollection`` specifications."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any

import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots

from quantas_gui.renderers.plotly.common import (
    apply_layout,
    array,
    axis_title,
    colorscale,
    limits,
    line_dash,
    marker_symbol,
    series_color,
    subplot_grid,
)
from quantas_gui.renderers.plotly.options import PlotlyRenderOptions


@dataclass(frozen=True, slots=True)
class PlotControlProfile:
    """Controls applicable to one plot specification family."""

    colormap: bool = False
    hover: bool = True
    projection: bool = False
    contour: bool = False
    surface: bool = False
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
        return {"label": f"{self.group} · {self.title}", "value": self.key}

    def as_dict(self) -> dict[str, Any]:
        """Return a bounded JSON-safe descriptor."""
        return {
            "key": self.key, "title": self.title, "kind": self.kind,
            "family_key": self.family_key, "group": self.group,
            "description": self.description, "controls": self.controls.as_dict(),
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
        kind = type(spec).__name__
        descriptors.append(
            PlotDescriptor(
                key=key,
                title=title,
                kind=kind,
                family_key=family_key,
                group=(group_resolver(title, kind, family_key) if group_resolver else "Figures"),
                description=(description_resolver(title, kind, family_key) if description_resolver else ""),
                controls=_control_profile(kind),
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
    renderer = {
        "LinePlotSpec": _line_plot,
        "ContourPlotSpec": _contour_plot,
        "PolarPlotSpec": _polar_plot,
        "SurfacePlotSpec": _surface_plot,
        "SphericalMapSpec": _spherical_map,
        "SphericalSummarySpec": _spherical_summary,
        "PanelPlotSpec": _panel_plot,
    }.get(type(spec).__name__)
    if renderer is None:
        raise TypeError(f"unsupported Quantas plot specification {type(spec).__name__!r}")
    return renderer(spec, resolved)


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
                    name=str(band.label),
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
                    name=str(band.label),
                    hoverinfo="skip",
                )
            )

    for index, series in enumerate(getattr(spec, "series", ())):
        _add_cartesian_series(figure, series, index=index)

    for index, path in enumerate(getattr(spec, "colored_paths", ())):
        _add_colored_path(figure, path, index=index, override_colormap=options.colormap)

    for span in getattr(spec, "spans", ()):
        color = getattr(span, "color", None) or "#7f9bad"
        arguments = {
            "fillcolor": color,
            "opacity": float(getattr(span, "alpha", 0.25)),
            "line_width": 0,
            "layer": "below",
            "annotation_text": str(getattr(span, "label", "")),
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
    return apply_layout(
        figure,
        title=str(spec.title),
        options=_merge_options(options, show_legend=bool(getattr(spec, "show_legend", True))),
    )


def _contour_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    figure = go.Figure()
    lower, upper = limits(getattr(spec, "value_limits", None))
    selected_colormap = options.colormap or getattr(spec, "colormap", "viridis")
    contour = go.Contour(
        x=array(spec.x),
        y=array(spec.y),
        z=array(spec.z),
        colorscale=colorscale(selected_colormap),
        zmin=lower,
        zmax=upper,
        contours={
            "coloring": "heatmap" if getattr(spec, "mode", "smooth") == "smooth" else "fill",
            "showlines": (bool(getattr(spec, "isolines", True))
                          if options.show_isolines is None else options.show_isolines),
            "showlabels": (bool(getattr(spec, "isoline_labels", False))
                           if options.show_isoline_labels is None else options.show_isoline_labels),
        },
        showscale=options.show_colorbar,
        colorbar={"title": axis_title(spec.value_axis)},
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
                colorscale=[[0.0, "rgba(240,108,117,0.12)"], [1.0, "rgba(240,108,117,0.12)"]],
                showscale=False,
                contours={"coloring": "fill", "showlines": False},
                hoverinfo="skip",
                name=str(mask.label),
            )
        )

    for index, series in enumerate(getattr(spec, "series", ())):
        _add_cartesian_series(figure, series, index=index)
    for index, path in enumerate(getattr(spec, "colored_paths", ())):
        _add_colored_path(figure, path, index=index, override_colormap=options.colormap)

    figure.update_xaxes(title_text=axis_title(spec.x_axis))
    figure.update_yaxes(title_text=axis_title(spec.y_axis))
    _apply_axis_limits(figure, spec.x_axis, axis="x")
    _apply_axis_limits(figure, spec.y_axis, axis="y")
    return apply_layout(figure, title=str(spec.title), options=options)


def _polar_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    panels = list(getattr(spec, "panels", ()))
    rows, columns = subplot_grid(len(panels), int(getattr(spec, "legend_columns", 2)))
    figure = make_subplots(
        rows=rows,
        cols=columns,
        specs=[[{"type": "polar"} for _ in range(columns)] for _ in range(rows)],
        subplot_titles=[str(panel.title) for panel in panels],
    )
    for panel_index, panel in enumerate(panels):
        row = panel_index // columns + 1
        column = panel_index % columns + 1
        for series_index, series in enumerate(panel.series):
            style = series.style
            mode = "lines+markers" if getattr(style, "marker", None) else "lines"
            theta = array(series.x)
            if getattr(panel, "angle_unit", "degree") == "radian":
                theta = np.degrees(theta)
            figure.add_trace(
                go.Scatterpolar(
                    theta=theta,
                    r=array(series.y),
                    mode=mode,
                    name=str(series.label),
                    line={
                        "color": series_color(series_index, getattr(style, "color", None)),
                        "width": float(getattr(style, "line_width", 1.5)),
                        "dash": line_dash(getattr(style, "line_style", "solid")),
                    },
                    marker={
                        "symbol": marker_symbol(getattr(style, "marker", None)),
                        "size": float(getattr(style, "marker_size", 6.0) or 6.0),
                    },
                ),
                row=row,
                col=column,
            )
        polar_name = "polar" if panel_index == 0 else f"polar{panel_index + 1}"
        figure.layout[polar_name].update(
            radialaxis={
                "range": None
                if getattr(panel, "radial_limit", None) is None
                else [0.0, float(panel.radial_limit)],
                "showgrid": options.show_grid,
                "visible": options.show_axes,
            },
            angularaxis={
                "direction": "counterclockwise"
                if int(getattr(panel, "theta_direction", 1)) >= 0
                else "clockwise",
                "rotation": _polar_rotation(getattr(panel, "theta_zero_location", "N")),
                "showgrid": options.show_grid,
                "visible": options.show_axes,
            },
            bgcolor="#071522" if options.template == "quantas_dark" else "#ffffff",
        )
    return apply_layout(
        figure,
        title=str(spec.title),
        options=_merge_options(options, show_legend=bool(getattr(spec, "show_legend", True))),
    )


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
            "name": str(layer.label),
            "opacity": (float(getattr(style, "opacity", 1.0))
                        if options.surface_opacity is None else options.surface_opacity),
            "showscale": bool(getattr(style, "show_colorbar", True)) and options.show_colorbar,
            "cmin": lower,
            "cmax": upper,
            "colorbar": {"title": axis_title(spec.value_axis)},
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

    for vector_index, vector_layer in enumerate(getattr(spec, "vector_layers", ())):
        _add_vector_layer(figure, vector_layer, index=vector_index)

    if bool(getattr(spec, "equal_aspect", True)):
        figure.update_layout(scene_aspectmode="data")
    if not bool(getattr(spec, "show_axes", True)):
        figure.update_layout(
            scene={
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "zaxis": {"visible": False},
            }
        )
    return apply_layout(figure, title=str(spec.title), options=options, three_dimensional=True)


def _spherical_map(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    figure = go.Figure()
    projection = (
        getattr(spec, "projection", "equal_area")
        if options.projection == "source"
        else options.projection
    )
    theta = array(spec.theta)
    phi = array(spec.phi)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    x, y = _project_angles(
        theta_grid,
        phi_grid,
        hemisphere=str(getattr(spec, "hemisphere", "upper")),
        projection=str(projection),
    )
    lower, upper = limits(getattr(spec.value_axis, "limits", None))
    selected_colormap = options.colormap or getattr(spec, "colormap", "viridis")
    values = array(spec.values).ravel()
    point_count = max(1, values.size)
    marker_size = max(3.0, min(10.0, 220.0 / np.sqrt(point_count)))
    figure.add_trace(
        go.Scattergl(
            x=x.ravel(),
            y=y.ravel(),
            mode="markers",
            marker={
                "size": marker_size,
                "color": values,
                "colorscale": colorscale(selected_colormap),
                "cmin": lower,
                "cmax": upper,
                "showscale": True,
                "colorbar": {"title": axis_title(spec.value_axis)},
                "line": {"width": 0},
            },
            customdata=values,
            name=str(spec.title),
            hovertemplate=(
                "map x: %{x:.5g}<br>map y: %{y:.5g}<br>"
                f"{axis_title(spec.value_axis)}: %{{customdata:.6g}}<extra></extra>"
            ),
        )
    )
    _add_spherical_markers(figure, spec, projection=str(projection))
    _add_axis_fields(figure, spec, projection=str(projection))
    figure.update_yaxes(scaleanchor="x", scaleratio=1)
    return apply_layout(figure, title=str(spec.title), options=options)


def _spherical_summary(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    maps = list(getattr(spec, "maps", ()))
    rows, columns = subplot_grid(len(maps), int(getattr(spec, "columns", 3)))
    figure = make_subplots(
        rows=rows,
        cols=columns,
        subplot_titles=[str(item.title) for item in maps],
        horizontal_spacing=0.08,
        vertical_spacing=0.12,
    )
    for index, map_spec in enumerate(maps):
        row = index // columns + 1
        column = index % columns + 1
        child = _spherical_map(map_spec, options)
        for trace in child.data:
            cloned = go.Figure(data=[trace]).data[0]
            if hasattr(cloned, "showscale"):
                cloned.showscale = index == len(maps) - 1
            figure.add_trace(cloned, row=row, col=column)
        figure.update_xaxes(scaleanchor=f"y{index + 1 if index else ''}", row=row, col=column)
    return apply_layout(figure, title=str(spec.title), options=options)


def _panel_plot(spec: Any, options: PlotlyRenderOptions) -> go.Figure:
    panels = list(getattr(spec, "panels", ()))
    rows, columns = subplot_grid(len(panels), int(getattr(spec, "columns", 2)))
    figure = make_subplots(
        rows=rows,
        cols=columns,
        subplot_titles=[str(panel.title) for panel in panels],
        shared_xaxes=bool(getattr(spec, "share_x", False)),
        shared_yaxes=bool(getattr(spec, "share_y", False)),
    )
    for index, panel in enumerate(panels):
        row = index // columns + 1
        column = index % columns + 1
        child = render_plot(panel, options=options)
        for trace in child.data:
            figure.add_trace(go.Figure(data=[trace]).data[0], row=row, col=column)
        if hasattr(panel, "x_axis"):
            figure.update_xaxes(title_text=axis_title(panel.x_axis), row=row, col=column)
        if hasattr(panel, "y_axis"):
            figure.update_yaxes(title_text=axis_title(panel.y_axis), row=row, col=column)
    return apply_layout(figure, title=str(spec.title), options=options)



def _add_scalar_background(
    figure: go.Figure,
    background: Any,
    *,
    override_colormap: str | None,
) -> None:
    """Approximate one-dimensional scalar backgrounds with bounded spans."""
    coordinates = array(background.coordinates).astype(float).ravel()
    values = array(background.values).astype(float).ravel()
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
                        "title": str(secondary.label),
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
                        "title": str(secondary.label),
                        "overlaying": "x",
                        "side": "bottom" if location == "bottom" else "top",
                        "tickmode": "array",
                        "tickvals": positions,
                        "ticktext": labels,
                        "showgrid": False,
                    }
                }
            )

def _add_cartesian_series(figure: go.Figure, series: Any, *, index: int) -> None:
    style = series.style
    marker = getattr(style, "marker", None)
    mode = "lines+markers" if marker else "lines"
    color = series_color(index, getattr(style, "color", None))
    figure.add_trace(
        go.Scattergl(
            x=array(series.x),
            y=array(series.y),
            mode=mode,
            name=str(series.label),
            opacity=float(getattr(style, "alpha", 1.0)),
            line={
                "color": color,
                "width": float(getattr(style, "line_width", 1.5)),
                "dash": line_dash(getattr(style, "line_style", "solid")),
            },
            marker={
                "symbol": marker_symbol(marker),
                "size": float(getattr(style, "marker_size", 6.0) or 6.0),
                "color": color,
                "line": {
                    "color": getattr(style, "marker_edge_color", None) or "#04101a",
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
    override_colormap: str | None,
) -> None:
    style = path.style
    lower, upper = limits(getattr(style, "value_limits", None))
    selected = override_colormap or getattr(style, "colormap", "viridis")
    figure.add_trace(
        go.Scattergl(
            x=array(path.x),
            y=array(path.y),
            mode="lines+markers",
            name=str(path.label),
            line={
                "color": series_color(index, None),
                "width": float(getattr(style, "line_width", 1.8)),
                "dash": line_dash(getattr(style, "line_style", "solid")),
            },
            marker={
                "color": array(path.values),
                "colorscale": colorscale(selected),
                "cmin": lower,
                "cmax": upper,
                "showscale": bool(getattr(style, "show_colorbar", True)),
                "colorbar": {"title": axis_title(path.value_axis)},
                "size": float(getattr(style, "marker_size", 5.0) or 5.0),
            },
            customdata=array(path.values),
            hovertemplate=(
                "x: %{x:.8g}<br>y: %{y:.8g}<br>"
                f"{axis_title(path.value_axis)}: %{{customdata:.8g}}<extra></extra>"
            ),
        )
    )


def _add_vector_layer(figure: go.Figure, layer: Any, *, index: int) -> None:
    origins = array(layer.origins)
    vectors = array(layer.vectors)
    style = layer.style
    color = series_color(index, getattr(style, "color", None))
    scale = float(getattr(style, "scale", 1.0))
    resolved = getattr(layer, "resolved_mask", None)
    if resolved is not None:
        mask = array(resolved).astype(bool)
        origins = origins[mask]
        vectors = vectors[mask]
    if bool(getattr(layer, "axial", False)):
        half = 0.5 * scale * vectors
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
                line={"color": color, "width": float(getattr(style, "line_width", 1.0))},
                opacity=float(getattr(style, "opacity", 1.0)),
                name=str(layer.label),
                hoverinfo="skip",
            )
        )
    else:
        vectors = vectors * scale
        figure.add_trace(
            go.Cone(
                x=origins[:, 0],
                y=origins[:, 1],
                z=origins[:, 2],
                u=vectors[:, 0],
                v=vectors[:, 1],
                w=vectors[:, 2],
                colorscale=[[0.0, color], [1.0, color]],
                showscale=False,
                sizemode="absolute",
                sizeref=max(scale, 1.0e-12),
                opacity=float(getattr(style, "opacity", 1.0)),
                name=str(layer.label),
            )
        )


def _add_spherical_markers(figure: go.Figure, spec: Any, *, projection: str) -> None:
    for index, marker in enumerate(getattr(spec, "markers", ())):
        directions = array(marker.directions)
        theta, phi = _directions_to_angles(directions)
        x, y = _project_angles(
            theta,
            phi,
            hemisphere=str(getattr(spec, "hemisphere", "upper")),
            projection=projection,
        )
        figure.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker={
                    "symbol": marker_symbol(getattr(marker, "marker", "circle")),
                    "size": 9,
                    "color": series_color(index, None),
                    "line": {"color": "#04101a", "width": 1},
                },
                name=str(marker.label),
                hovertemplate="map x: %{x:.5g}<br>map y: %{y:.5g}<extra>%{fullData.name}</extra>",
            )
        )


def _add_axis_fields(figure: go.Figure, spec: Any, *, projection: str) -> None:
    for index, layer in enumerate(getattr(spec, "axis_layers", ())):
        directions = array(layer.directions)
        axes = array(layer.axes)
        resolved = getattr(layer, "resolved_mask", None)
        if resolved is not None:
            mask = array(resolved).astype(bool)
            directions = directions[mask]
            axes = axes[mask]
        theta, phi = _directions_to_angles(directions)
        x, y = _project_angles(
            theta,
            phi,
            hemisphere=str(getattr(spec, "hemisphere", "upper")),
            projection=projection,
        )
        tangent = axes[:, :2]
        norm = np.linalg.norm(tangent, axis=1)
        norm[norm == 0.0] = 1.0
        tangent = tangent / norm[:, None] * 0.025
        segments_x: list[float | None] = []
        segments_y: list[float | None] = []
        for origin_x, origin_y, vector in zip(x, y, tangent, strict=True):
            segments_x.extend([origin_x - vector[0], origin_x + vector[0], None])
            segments_y.extend([origin_y - vector[1], origin_y + vector[1], None])
        figure.add_trace(
            go.Scatter(
                x=segments_x,
                y=segments_y,
                mode="lines",
                line={"color": series_color(index, None), "width": 1},
                name=str(layer.label),
                hoverinfo="skip",
            )
        )


def _project_angles(
    theta: np.ndarray,
    phi: np.ndarray,
    *,
    hemisphere: str,
    projection: str,
) -> tuple[np.ndarray, np.ndarray]:
    if hemisphere == "full":
        return np.degrees(phi), 90.0 - np.degrees(theta)
    alpha = np.asarray(theta, dtype=float)
    if hemisphere == "lower":
        alpha = pi - alpha
    if projection == "stereographic":
        radius = np.tan(alpha / 2.0)
    else:
        radius = np.sqrt(2.0) * np.sin(alpha / 2.0)
    return radius * np.sin(phi), radius * np.cos(phi)


def _directions_to_angles(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    normalized = directions / np.linalg.norm(directions, axis=1)[:, None]
    theta = np.arccos(np.clip(normalized[:, 2], -1.0, 1.0))
    phi = np.arctan2(normalized[:, 1], normalized[:, 0])
    return theta, phi


def _apply_axis_limits(figure: go.Figure, axis_spec: Any, *, axis: str) -> None:
    lower, upper = limits(getattr(axis_spec, "limits", None))
    if lower is None and upper is None:
        return
    range_value = [lower, upper]
    if axis == "x":
        figure.update_xaxes(range=range_value)
    else:
        figure.update_yaxes(range=range_value)


def _polar_rotation(location: str) -> float:
    return {"N": 90.0, "E": 0.0, "S": -90.0, "W": 180.0}.get(str(location).upper(), 90.0)


def _merge_options(options: PlotlyRenderOptions, *, show_legend: bool) -> PlotlyRenderOptions:
    return PlotlyRenderOptions(
        colormap=options.colormap,
        show_legend=options.show_legend and show_legend,
        show_grid=options.show_grid,
        show_axes=options.show_axes,
        show_colorbar=options.show_colorbar,
        show_isolines=options.show_isolines,
        show_isoline_labels=options.show_isoline_labels,
        surface_opacity=options.surface_opacity,
        hover_mode=options.hover_mode,
        projection=options.projection,
        camera=options.camera,
        template=options.template,
        uirevision=options.uirevision,
    )


def _control_profile(kind: str) -> PlotControlProfile:
    """Return controls that are meaningful for one public PlotSpec kind."""
    if kind == "ContourPlotSpec":
        return PlotControlProfile(colormap=True, contour=True)
    if kind == "SurfacePlotSpec":
        return PlotControlProfile(colormap=True, surface=True, grid=False)
    if kind in {"SphericalMapSpec", "SphericalSummarySpec"}:
        return PlotControlProfile(colormap=True, projection=True, grid=False)
    if kind == "PolarPlotSpec":
        return PlotControlProfile(grid=True, axes=True)
    if kind == "PanelPlotSpec":
        return PlotControlProfile(colormap=True, projection=True, contour=True, surface=True)
    return PlotControlProfile()


def _rgba(color: str, alpha: float) -> str:
    if color.startswith("#") and len(color) == 7:
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        return f"rgba({red},{green},{blue},{alpha:.4g})"
    return color
