"""Scientific plot selection, cached PlotSpec rendering, and display controls."""

from __future__ import annotations

import logging

import dash
from dash import ALL, Input, Output, State, html, no_update

from quantas_gui.callbacks.result_helpers import (
    default_selector_values,
    empty_figure,
    plot_build_selection,
    plot_control_configuration,
    plot_kind_label,
    reference_from_session,
    selection_summary,
    source_optional_float,
    source_optional_string,
)
from quantas_gui.components.renderer_controls import PLOT_APPEARANCE_DEFAULTS, family_note
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.components.results import (
    active_scientific_summary,
    empty_result_section,
    loaded_plot_selector,
    scientific_selection_panel,
)
from quantas_gui.explorer.models import PlotBuildSelection
from quantas_gui.presentation.scientific_labels import scientific_label_text
from quantas_gui.renderers.plotly import (
    PlotlyRenderOptions,
    plot_inventory,
    render_collection_plot,
)
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.services.results import ResultExplorerService

_LOGGER = logging.getLogger(__name__)


def register_result_plot_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register scientific and presentation-level plot callbacks."""

    @app.callback(
        Output(ResultIds.PLOT_SCIENCE_HOST, "children"),
        Output(ResultIds.PLOT_FAMILY_INFO, "children"),
        Output(ResultIds.PLOT_SELECTOR_HOST, "children"),
        Output(ResultIds.PLOT_INVENTORY, "data"),
        Output(ResultIds.PLOT_SCIENCE_SELECTION, "data"),
        Output(ResultIds.PLOT_VIEW, "figure"),
        Output(ResultIds.PLOT_ACTIVE_SUMMARY, "children"),
        Input(ResultIds.PLOT_FAMILY, "value"),
        State(ResultIds.SESSION, "data"),
        State("q-effective-theme", "data"),
        prevent_initial_call=True,
    )
    def configure_scientific_selection(family_key, session, effective_theme):
        if not session or not family_key:
            return (no_update,) * 7
        reference = reference_from_session(session)
        try:
            families = service.plot_families(reference)
            selected_family = next((item for item in families if item.key == family_key), None)
            schema = service.plot_selection_schema(reference, family_key)
            return (
                scientific_selection_panel(schema),
                family_note(selected_family),
                html.Div(),
                [],
                None,
                empty_figure(
                    "Choose the scientific properties and context, then build the view.",
                    theme=str(effective_theme or "dark"),
                ),
                html.Div(),
            )
        except Exception as exc:
            _LOGGER.exception("Unable to prepare scientific plot selections")
            return (
                empty_result_section(
                    "Unable to prepare scientific selections",
                    public_error_message(exc),
                ),
                no_update,
                html.Div(),
                [],
                None,
                empty_figure(
                    f"Unable to prepare this plot family: {public_error_message(exc)}",
                    theme=str(effective_theme or "dark"),
                ),
                html.Div(),
            )

    @app.callback(
        Output(ResultIds.PLOT_SELECTOR_HOST, "children", allow_duplicate=True),
        Output(ResultIds.PLOT_INVENTORY, "data", allow_duplicate=True),
        Output(ResultIds.PLOT_SCIENCE_SELECTION, "data", allow_duplicate=True),
        Output(ResultIds.PLOT_VIEW, "figure", allow_duplicate=True),
        Output(ResultIds.PLOT_ACTIVE_SUMMARY, "children", allow_duplicate=True),
        Input(ResultIds.PLOT_SCIENCE_APPLY, "n_clicks"),
        State({"type": ResultIds.PLOT_SCIENCE_PROPERTY, "key": ALL}, "value"),
        State({"type": ResultIds.PLOT_SCIENCE_PROPERTY, "key": ALL}, "id"),
        State({"type": ResultIds.PLOT_SCIENCE_CONTEXT, "key": ALL}, "value"),
        State({"type": ResultIds.PLOT_SCIENCE_CONTEXT, "key": ALL}, "id"),
        State(ResultIds.PLOT_FAMILY, "value"),
        State(ResultIds.SESSION, "data"),
        State("q-effective-theme", "data"),
        prevent_initial_call=True,
    )
    def build_scientific_plot_family(
        clicks,
        property_values,
        property_ids,
        context_values,
        context_ids,
        family_key,
        session,
        effective_theme,
    ):
        if not clicks or not session or not family_key:
            return (no_update,) * 5
        selection = plot_build_selection(
            family_key,
            property_values or (),
            property_ids or (),
            context_values or (),
            context_ids or (),
        )
        reference = reference_from_session(session)
        try:
            schema = service.plot_selection_schema(reference, family_key)
            collection = service.build_plots(reference, family_key, selection=selection)
            inventory = plot_inventory(
                collection,
                family_key=family_key,
                group_resolver=lambda title, kind, family: service.plot_group(
                    reference, title, kind, family
                ),
                description_resolver=lambda title, kind, family: service.plot_description(
                    reference, title, kind, family
                ),
            )
            warnings = tuple(str(item) for item in getattr(collection, "warnings", ()))
            figure = (
                render_collection_plot(
                    collection,
                    inventory[0].key,
                    options=PlotlyRenderOptions(
                        template=("plotly_white" if effective_theme == "light" else "quantas_dark"),
                        uirevision=inventory[0].key,
                    ),
                )
                if inventory
                else empty_figure(
                    "No figures were generated for this selection.",
                    theme=str(effective_theme or "dark"),
                )
            )
            summary = active_scientific_summary(selection_summary(schema, selection))
            return (
                loaded_plot_selector(inventory, warnings=warnings),
                [item.as_dict() for item in inventory],
                selection.as_dict(),
                figure,
                summary,
            )
        except Exception as exc:
            _LOGGER.exception("Unable to build the selected scientific plots")
            return (
                empty_result_section(
                    "Unable to build this scientific selection",
                    public_error_message(exc),
                ),
                [],
                selection.as_dict(),
                empty_figure(
                    f"Unable to build figures: {public_error_message(exc)}",
                    theme=str(effective_theme or "dark"),
                ),
                html.Div(),
            )

    @app.callback(
        Output(ResultIds.PLOT_SCIENCE_STATUS, "children"),
        Output(ResultIds.PLOT_SCIENCE_STATUS, "className"),
        Input({"type": ResultIds.PLOT_SCIENCE_PROPERTY, "key": ALL}, "value"),
        Input({"type": ResultIds.PLOT_SCIENCE_CONTEXT, "key": ALL}, "value"),
        Input(ResultIds.PLOT_FAMILY, "value"),
        Input(ResultIds.PLOT_SCIENCE_SELECTION, "data"),
        State({"type": ResultIds.PLOT_SCIENCE_PROPERTY, "key": ALL}, "id"),
        State({"type": ResultIds.PLOT_SCIENCE_CONTEXT, "key": ALL}, "id"),
        prevent_initial_call=True,
    )
    def update_scientific_selection_status(
        property_values,
        context_values,
        family_key,
        built_selection,
        property_ids,
        context_ids,
    ):
        if not family_key:
            return "Not built yet", "q-scientific-selection-status is-pending"
        pending = plot_build_selection(
            family_key,
            property_values or (),
            property_ids or (),
            context_values or (),
            context_ids or (),
        )
        built = PlotBuildSelection.from_dict(built_selection)
        if built is None:
            return "Not built yet", "q-scientific-selection-status is-pending"
        if pending.cache_token() != built.cache_token():
            return (
                "Selection changed — rebuild required",
                "q-scientific-selection-status is-dirty",
            )
        return "Showing current selection", "q-scientific-selection-status is-current"

    @app.callback(
        Output({"type": ResultIds.PLOT_SCIENCE_PROPERTY, "key": ALL}, "value"),
        Output({"type": ResultIds.PLOT_SCIENCE_CONTEXT, "key": ALL}, "value"),
        Input(ResultIds.PLOT_SCIENCE_RESET, "n_clicks"),
        State({"type": ResultIds.PLOT_SCIENCE_PROPERTY, "key": ALL}, "id"),
        State({"type": ResultIds.PLOT_SCIENCE_CONTEXT, "key": ALL}, "id"),
        State(ResultIds.PLOT_FAMILY, "value"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def reset_scientific_selection(
        clicks,
        property_ids,
        context_ids,
        family_key,
        session,
    ):
        if not clicks or not session or not family_key:
            return no_update, no_update
        schema = service.plot_selection_schema(reference_from_session(session), family_key)
        return default_selector_values(schema, property_ids or (), context_ids or ())

    @app.callback(
        Output(ResultIds.PLOT_DESCRIPTION, "children"),
        Output(ResultIds.PLOT_CONTROL_CONTEXT, "children"),
        Output(ResultIds.PLOT_HOVER_WRAP, "className"),
        Output(ResultIds.PLOT_DISPLAY_WRAP, "className"),
        Output(ResultIds.PLOT_LINE_WRAP, "className"),
        Output(ResultIds.PLOT_COLORMAP_WRAP, "className"),
        Output(ResultIds.PLOT_AXIS_LABEL_WRAP, "className"),
        Output(ResultIds.PLOT_PROJECTION_WRAP, "className"),
        Output(ResultIds.PLOT_CONTOUR_WRAP, "className"),
        Output(ResultIds.PLOT_POLARIZATION_WRAP, "className"),
        Output(ResultIds.PLOT_SURFACE_WRAP, "className"),
        Output(ResultIds.PLOT_OPTIONS, "options"),
        Output(ResultIds.PLOT_OPTIONS, "value"),
        Input(ResultIds.PLOT_SELECTOR, "value"),
        State(ResultIds.PLOT_INVENTORY, "data"),
        prevent_initial_call=True,
    )
    def configure_plot_controls(selected, inventory):
        descriptor = next(
            (item for item in (inventory or []) if item.get("key") == selected),
            None,
        )
        if descriptor is None:
            return "", "Select a figure", *plot_control_configuration({})
        controls = dict(descriptor.get("controls", {}))
        kind = str(descriptor.get("kind", ""))
        description = html.Div(
            [
                html.Strong(scientific_label_text(descriptor.get("title", "Figure"))),
                html.Span(scientific_label_text(descriptor.get("description", ""))),
                html.Small(f"{descriptor.get('group', 'Figures')} · {kind}"),
            ]
        )
        return (
            description,
            f"{plot_kind_label(kind)} · display only",
            *plot_control_configuration(controls),
        )

    @app.callback(
        Output(ResultIds.PLOT_VIEW, "figure", allow_duplicate=True),
        Input(ResultIds.PLOT_SELECTOR, "value"),
        Input(ResultIds.PLOT_COLORMAP, "value"),
        Input(ResultIds.PLOT_OPTIONS, "value"),
        Input(ResultIds.PLOT_HOVER, "value"),
        Input(ResultIds.PLOT_LINE_WIDTH, "value"),
        Input(ResultIds.PLOT_LINE_COLOR, "value"),
        Input(ResultIds.PLOT_AXIS_LABEL_MODE, "value"),
        Input(ResultIds.PLOT_PROJECTION, "value"),
        Input(ResultIds.PLOT_CONTOUR_OPTIONS, "value"),
        Input(ResultIds.PLOT_CONTOUR_LEVELS, "value"),
        Input(ResultIds.PLOT_POLARIZATION, "value"),
        Input(ResultIds.PLOT_POLARIZATION_STRIDE, "value"),
        Input(ResultIds.PLOT_POLARIZATION_WIDTH, "value"),
        Input(ResultIds.PLOT_POLARIZATION_SCALE, "value"),
        Input(ResultIds.PLOT_POLARIZATION_COLOR, "value"),
        Input(ResultIds.PLOT_SURFACE_OPACITY, "value"),
        Input(ResultIds.PLOT_CAMERA, "value"),
        Input(ResultIds.PLOT_COLORBAR, "value"),
        Input("q-effective-theme", "data"),
        State(ResultIds.PLOT_FAMILY, "value"),
        State(ResultIds.PLOT_SCIENCE_SELECTION, "data"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def render_selected_plot(
        selected,
        colormap,
        toggles,
        hover_mode,
        line_width,
        line_color,
        axis_label_mode,
        projection,
        contour_options,
        contour_levels,
        polarization_options,
        polarization_stride,
        polarization_width,
        polarization_scale,
        polarization_color,
        opacity,
        camera,
        colorbar,
        effective_theme,
        family_key,
        selection_data,
        session,
    ):
        if not session or not selected or not family_key:
            return empty_figure("Select a figure", theme=str(effective_theme or "dark"))
        active = set(toggles or ())
        contour = set(contour_options or ())
        polarizations = set(polarization_options or ())
        try:
            collection = service.build_plots(
                reference_from_session(session),
                family_key,
                selection=PlotBuildSelection.from_dict(selection_data),
            )
            options = PlotlyRenderOptions(
                colormap=source_optional_string(colormap),
                line_width=source_optional_float(line_width),
                line_color=source_optional_string(line_color),
                show_legend="legend" in active,
                show_grid="grid" in active,
                show_axes="axes" in active,
                axis_label_mode=axis_label_mode or "cartesian",
                show_colorbar="colorbar" in set(colorbar or ()),
                show_isolines="isolines" in contour,
                show_isoline_labels="labels" in contour,
                contour_levels=(
                    int(contour_levels) if contour_levels not in (None, 0, "0") else None
                ),
                surface_opacity=float(opacity) if opacity is not None else None,
                show_polarizations="polarization" in polarizations,
                polarization_stride=max(1, int(polarization_stride or 1)),
                polarization_line_width=source_optional_float(polarization_width),
                polarization_scale=source_optional_float(polarization_scale),
                polarization_color=source_optional_string(polarization_color),
                hover_mode=hover_mode or "closest",
                projection=projection or "source",
                camera=camera or "source",
                template=("plotly_white" if effective_theme == "light" else "quantas_dark"),
                uirevision=str(selected),
            )
            return render_collection_plot(collection, selected, options=options)
        except Exception as exc:
            _LOGGER.exception("Unable to render the selected PlotSpec")
            return empty_figure(
                f"Unable to render figure: {public_error_message(exc)}",
                theme=str(effective_theme or "dark"),
            )

    @app.callback(
        Output(ResultIds.PLOT_COLORMAP, "value"),
        Output(ResultIds.PLOT_OPTIONS, "value", allow_duplicate=True),
        Output(ResultIds.PLOT_HOVER, "value"),
        Output(ResultIds.PLOT_LINE_WIDTH, "value"),
        Output(ResultIds.PLOT_LINE_COLOR, "value"),
        Output(ResultIds.PLOT_AXIS_LABEL_MODE, "value"),
        Output(ResultIds.PLOT_PROJECTION, "value"),
        Output(ResultIds.PLOT_CONTOUR_OPTIONS, "value"),
        Output(ResultIds.PLOT_CONTOUR_LEVELS, "value"),
        Output(ResultIds.PLOT_POLARIZATION, "value"),
        Output(ResultIds.PLOT_POLARIZATION_STRIDE, "value"),
        Output(ResultIds.PLOT_POLARIZATION_WIDTH, "value"),
        Output(ResultIds.PLOT_POLARIZATION_SCALE, "value"),
        Output(ResultIds.PLOT_POLARIZATION_COLOR, "value"),
        Output(ResultIds.PLOT_SURFACE_OPACITY, "value"),
        Output(ResultIds.PLOT_CAMERA, "value"),
        Output(ResultIds.PLOT_COLORBAR, "value"),
        Input(ResultIds.PLOT_APPEARANCE_RESET, "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_plot_appearance(clicks):
        if not clicks:
            return (no_update,) * 17
        defaults = PLOT_APPEARANCE_DEFAULTS
        return (
            defaults["colormap"],
            list(defaults["visibility"]),
            defaults["hover"],
            defaults["line_width"],
            defaults["line_color"],
            defaults["axis_label_mode"],
            defaults["projection"],
            list(defaults["contour_options"]),
            defaults["contour_levels"],
            list(defaults["polarization"]),
            defaults["polarization_stride"],
            defaults["polarization_width"],
            defaults["polarization_scale"],
            defaults["polarization_color"],
            defaults["surface_opacity"],
            defaults["camera"],
            list(defaults["colorbar"]),
        )
