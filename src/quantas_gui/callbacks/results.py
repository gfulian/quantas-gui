"""Callbacks for lazy native-HDF5 result inspection and rendering."""

from __future__ import annotations

from contextlib import suppress
from typing import Any

import dash
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, dcc, html, no_update

from quantas_gui.components.renderer_controls import family_note
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.components.results import (
    alert,
    data_view,
    empty_result_section,
    loaded_plot_selector,
    message_timeline,
    messages_view,
    overview_view,
    plots_view,
    rendered_tables_view,
    result_header,
    tables_view,
)
from quantas_gui.models.results import ResultReference, ResultSummary
from quantas_gui.renderers.plotly import (
    PlotlyRenderOptions,
    plot_inventory,
    render_collection_plot,
)
from quantas_gui.renderers.tables import table_component, table_to_csv
from quantas_gui.services.result_backend import ResultBackendError
from quantas_gui.services.results import ResultExplorerService, ResultUploadError


def register_result_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register all Results Explorer callbacks against injected services."""

    @app.callback(
        Output(ResultIds.SESSION, "data"),
        Output(ResultIds.ALERT, "children"),
        Input(ResultIds.UPLOAD, "contents"),
        Input(ResultIds.UPLOAD_COMPACT, "contents"),
        Input(ResultIds.CLOSE, "n_clicks", allow_optional=True),
        State(ResultIds.UPLOAD, "filename"),
        State(ResultIds.UPLOAD_COMPACT, "filename"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def change_result(
        upload_contents,
        compact_contents,
        close_clicks,
        upload_filename,
        compact_filename,
        session,
    ):
        triggered = ctx.triggered_id
        if triggered == ResultIds.CLOSE and close_clicks:
            if session:
                with suppress(Exception):
                    service.close(_reference(session))
            return None, alert(
                "Result closed and local workspace removed.",
                level="success",
            )

        contents = compact_contents if triggered == ResultIds.UPLOAD_COMPACT else upload_contents
        filename = compact_filename if triggered == ResultIds.UPLOAD_COMPACT else upload_filename
        if not contents or not filename:
            return no_update, no_update

        try:
            reference, overview = service.ingest_upload(
                filename=filename,
                contents=contents,
            )
        except (
            ResultUploadError,
            ResultBackendError,
            ValueError,
            OSError,
        ) as exc:
            return no_update, alert(str(exc), level="error")
        except Exception as exc:
            return no_update, alert(
                f"Unable to open this native result: {exc}",
                level="error",
            )

        if session:
            with suppress(Exception):
                service.close(_reference(session))

        return {
            "reference": reference.as_dict(),
            "summary": overview.summary.as_dict(),
        }, alert(
            f"Opened {reference.filename} as {overview.summary.module_title}.",
            level="success",
        )

    @app.callback(
        Output(ResultIds.UPLOAD_PANEL, "className"),
        Output(ResultIds.WORKSPACE, "className"),
        Output(ResultIds.HEADER, "children"),
        Input(ResultIds.SESSION, "data"),
    )
    def render_session_shell(session):
        if not session:
            return (
                "q-panel q-result-open-panel",
                "q-result-workspace is-hidden",
                None,
            )
        return (
            "q-panel q-result-open-panel is-hidden",
            "q-result-workspace",
            result_header(_reference(session), _summary(session)),
        )

    @app.callback(
        Output(ResultIds.TAB_CONTENT, "children"),
        Input(ResultIds.TABS, "value"),
        Input(ResultIds.SESSION, "data"),
    )
    def render_tab(tab, session):
        if not session:
            return None
        reference = _reference(session)
        try:
            if tab == "tables":
                return tables_view(service.table_families(reference))
            if tab == "plots":
                return plots_view(service.plot_families(reference))
            overview = service.inspect(reference)
            if tab == "messages":
                return messages_view(overview)
            if tab == "data":
                return data_view(overview)
            return overview_view(reference, overview)
        except Exception as exc:
            return empty_result_section(
                "Unable to render this section",
                str(exc),
            )

    @app.callback(
        Output(ResultIds.TABLE_VIEW, "children"),
        Output(ResultIds.TABLE_FAMILY_INFO, "children"),
        Input(ResultIds.TABLE_FAMILY, "value"),
        State(ResultIds.TABLE_PAGE_SIZE, "value"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def load_table_family(family_key, page_size, session):
        if not session or not family_key:
            return no_update, no_update
        reference = _reference(session)
        try:
            families = service.table_families(reference)
            selected_family = next(
                (item for item in families if item.key == family_key),
                None,
            )
            tables = service.build_tables(reference, family_key)
            groups = tuple(service.table_group(reference, str(table.title)) for table in tables)
            return (
                rendered_tables_view(
                    tables,
                    page_size=int(page_size or 50),
                    groups=groups,
                ),
                family_note(selected_family),
            )
        except Exception as exc:
            return (
                empty_result_section(
                    "Unable to build this report family",
                    str(exc),
                ),
                no_update,
            )

    @app.callback(
        Output(ResultIds.TABLE_GRID, "children"),
        Input(ResultIds.TABLE_SELECTOR, "value"),
        Input(ResultIds.TABLE_PAGE_SIZE, "value"),
        State(ResultIds.TABLE_FAMILY, "value"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def render_selected_table(selected, page_size, family_key, session):
        if not session or selected is None:
            return no_update
        try:
            tables = service.build_tables(
                _reference(session),
                family_key,
            )
            return table_component(
                tables[int(selected)],
                component_id="q-result-table",
                page_size=int(page_size or 50),
            )
        except Exception as exc:
            return empty_result_section(
                "Unable to render the selected table",
                str(exc),
            )

    @app.callback(
        Output(ResultIds.PLOT_SELECTOR_HOST, "children"),
        Output(ResultIds.PLOT_INVENTORY, "data"),
        Output(ResultIds.PLOT_FAMILY_INFO, "children"),
        Output(ResultIds.PLOT_VIEW, "figure"),
        Input(ResultIds.PLOT_FAMILY, "value"),
        State(ResultIds.SESSION, "data"),
        State("q-effective-theme", "data"),
        prevent_initial_call=True,
    )
    def load_plot_family(family_key, session, effective_theme):
        if not session or not family_key:
            return no_update, no_update, no_update, no_update
        reference = _reference(session)
        try:
            families = service.plot_families(reference)
            selected_family = next(
                (item for item in families if item.key == family_key),
                None,
            )
            collection = service.build_plots(reference, family_key)
            inventory = plot_inventory(
                collection,
                family_key=family_key,
                group_resolver=lambda title, kind, family: service.plot_group(
                    reference,
                    title,
                    kind,
                    family,
                ),
                description_resolver=(
                    lambda title, kind, family: service.plot_description(
                        reference,
                        title,
                        kind,
                        family,
                    )
                ),
            )
            warnings = tuple(str(item) for item in getattr(collection, "warnings", ()))
            figure = _empty_figure(
                "Preparing selected figure…" if inventory else "No figures",
                theme=str(effective_theme or "dark"),
            )
            return (
                loaded_plot_selector(inventory, warnings=warnings),
                [item.as_dict() for item in inventory],
                family_note(selected_family),
                figure,
            )
        except Exception as exc:
            return (
                empty_result_section(
                    "Unable to build this plot family",
                    str(exc),
                ),
                [],
                no_update,
                _empty_figure(
                    f"Unable to build figures: {exc}",
                    theme=str(effective_theme or "dark"),
                ),
            )

    @app.callback(
        Output(ResultIds.PLOT_DESCRIPTION, "children"),
        Output(ResultIds.PLOT_COLORMAP_WRAP, "className"),
        Output(ResultIds.PLOT_HOVER_WRAP, "className"),
        Output(ResultIds.PLOT_PROJECTION_WRAP, "className"),
        Output(ResultIds.PLOT_CONTOUR_WRAP, "className"),
        Output(ResultIds.PLOT_SURFACE_WRAP, "className"),
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
            return "", *_control_classes({})
        controls = dict(descriptor.get("controls", {}))
        description = html.Div(
            [
                html.Strong(descriptor.get("title", "Figure")),
                html.Span(descriptor.get("description", "")),
                html.Small(f"{descriptor.get('group', 'Figures')} · {descriptor.get('kind', '')}"),
            ]
        )
        return description, *_control_classes(controls)

    @app.callback(
        Output(ResultIds.PLOT_VIEW, "figure", allow_duplicate=True),
        Input(ResultIds.PLOT_SELECTOR, "value"),
        Input(ResultIds.PLOT_COLORMAP, "value"),
        Input(ResultIds.PLOT_OPTIONS, "value"),
        Input(ResultIds.PLOT_HOVER, "value"),
        Input(ResultIds.PLOT_PROJECTION, "value"),
        Input(ResultIds.PLOT_CONTOUR_OPTIONS, "value"),
        Input(ResultIds.PLOT_SURFACE_OPACITY, "value"),
        Input(ResultIds.PLOT_CAMERA, "value"),
        Input(ResultIds.PLOT_COLORBAR, "value"),
        Input("q-effective-theme", "data"),
        State(ResultIds.PLOT_FAMILY, "value"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def render_selected_plot(
        selected,
        colormap,
        toggles,
        hover_mode,
        projection,
        contour_options,
        opacity,
        camera,
        colorbar,
        effective_theme,
        family_key,
        session,
    ):
        if not session or not selected or not family_key:
            return _empty_figure(
                "Select a figure",
                theme=str(effective_theme or "dark"),
            )
        active = set(toggles or ())
        contour = set(contour_options or ())
        try:
            collection = service.build_plots(
                _reference(session),
                family_key,
            )
            options = PlotlyRenderOptions(
                colormap=(None if colormap in (None, "source") else colormap),
                show_legend="legend" in active,
                show_grid="grid" in active,
                show_axes="axes" in active,
                show_colorbar="colorbar" in set(colorbar or ()),
                show_isolines="isolines" in contour,
                show_isoline_labels="labels" in contour,
                surface_opacity=(float(opacity) if opacity is not None else None),
                hover_mode=hover_mode or "closest",
                projection=projection or "source",
                camera=camera or "source",
                template=("plotly_white" if effective_theme == "light" else "quantas_dark"),
                uirevision=str(selected),
            )
            return render_collection_plot(
                collection,
                selected,
                options=options,
            )
        except Exception as exc:
            return _empty_figure(
                f"Unable to render figure: {exc}",
                theme=str(effective_theme or "dark"),
            )

    @app.callback(
        Output(ResultIds.MESSAGE_VIEW, "children"),
        Input(ResultIds.MESSAGE_LEVELS, "value"),
        Input(ResultIds.MESSAGE_SEARCH, "value"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def filter_messages(levels, query, session):
        if not session:
            return no_update
        try:
            overview = service.inspect(_reference(session))
        except Exception as exc:
            return empty_result_section(
                "Unable to load messages",
                str(exc),
            )
        active = set(levels or ())
        needle = (query or "").strip().lower()
        events = tuple(
            event
            for event in overview.events
            if (not active or event.level in active)
            and (not needle or needle in event.message.lower())
        )
        warnings = tuple(
            warning for warning in overview.warnings if not needle or needle in warning.lower()
        )
        return message_timeline(events, warnings)

    @app.callback(
        Output(ResultIds.DOWNLOAD_ORIGINAL_PAYLOAD, "data"),
        Input(ResultIds.DOWNLOAD_ORIGINAL, "n_clicks"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_original(clicks, session):
        if not clicks or not session:
            return no_update
        reference = _reference(session)
        return dcc.send_file(
            service.path(reference),
            filename=reference.filename,
        )

    @app.callback(
        Output(ResultIds.DOWNLOAD_REPORT_PAYLOAD, "data"),
        Input(ResultIds.DOWNLOAD_REPORT, "n_clicks"),
        State(
            ResultIds.TABLE_FAMILY,
            "value",
            allow_optional=True,
        ),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_plain_report(clicks, family_key, session):
        if not clicks or not session:
            return no_update
        reference = _reference(session)
        stem = reference.filename.rsplit(".", 1)[0]
        return dcc.send_string(
            service.render_plain_report(reference, family_key),
            filename=f"{stem}-report.txt",
        )

    @app.callback(
        Output(ResultIds.TABLE_DOWNLOAD_PAYLOAD, "data"),
        Input(ResultIds.TABLE_DOWNLOAD, "n_clicks"),
        State(ResultIds.TABLE_SELECTOR, "value"),
        State(ResultIds.TABLE_FAMILY, "value"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_selected_table(clicks, selected, family_key, session):
        if not clicks or not session or selected is None:
            return no_update
        table = service.build_tables(
            _reference(session),
            family_key,
        )[int(selected)]
        filename = f"{_safe_filename(str(table.title))}.csv"
        return dcc.send_string(
            table_to_csv(table),
            filename=filename,
        )


def _control_classes(
    controls: dict[str, Any],
) -> tuple[str, str, str, str, str]:
    def class_name(active: bool) -> str:
        return "q-plot-control" if active else "q-plot-control is-hidden"

    surface_class = (
        "q-plot-control q-plot-surface-controls"
        if controls.get("surface")
        else "q-plot-control q-plot-surface-controls is-hidden"
    )
    return (
        class_name(bool(controls.get("colormap"))),
        class_name(bool(controls.get("hover", True))),
        class_name(bool(controls.get("projection"))),
        class_name(bool(controls.get("contour"))),
        surface_class,
    )


def _reference(session: dict[str, Any]) -> ResultReference:
    return ResultReference.from_dict(dict(session["reference"]))


def _summary(session: dict[str, Any]) -> ResultSummary:
    return ResultSummary.from_dict(dict(session["summary"]))


def _safe_filename(value: str) -> str:
    cleaned = "".join(character if character.isalnum() else "-" for character in value.lower())
    return "-".join(part for part in cleaned.split("-") if part) or "quantas-table"


def _empty_figure(message: str, *, theme: str = "dark") -> go.Figure:
    figure = go.Figure()
    light = theme == "light"
    figure.update_layout(
        paper_bgcolor="#ffffff" if light else "#0d2030",
        plot_bgcolor="#f7fafc" if light else "#071522",
        font={"color": "#10283a" if light else "#ecf5fb"},
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {
                    "color": "#5f7482" if light else "#b3c7d5",
                    "size": 14,
                },
            }
        ],
    )
    return figure
