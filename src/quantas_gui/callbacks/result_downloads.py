"""Native result, report, table, and scientific-export downloads."""

from __future__ import annotations

import logging

import dash
from dash import Input, Output, State, dcc, no_update

from quantas_gui.callbacks.result_helpers import reference_from_session, safe_filename
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.components.results import alert
from quantas_gui.renderers.tables import table_to_csv
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.services.results import ResultExplorerService

_LOGGER = logging.getLogger(__name__)


def register_result_download_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register all Result Explorer download callbacks."""

    @app.callback(
        Output(ResultIds.DOWNLOAD_ORIGINAL_PAYLOAD, "data"),
        Input(ResultIds.DOWNLOAD_ORIGINAL, "n_clicks"),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_original(clicks, session):
        if not clicks or not session:
            return no_update
        reference = reference_from_session(session)
        return dcc.send_file(service.path(reference), filename=reference.filename)

    @app.callback(
        Output(ResultIds.DOWNLOAD_REPORT_PAYLOAD, "data"),
        Input(ResultIds.DOWNLOAD_REPORT, "n_clicks"),
        State(ResultIds.TABLE_FAMILY, "value", allow_optional=True),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_plain_report(clicks, family_key, session):
        if not clicks or not session:
            return no_update
        reference = reference_from_session(session)
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
        table = service.build_tables(reference_from_session(session), family_key)[int(selected)]
        return dcc.send_string(
            table_to_csv(table),
            filename=f"{safe_filename(str(table.title))}.csv",
        )

    @app.callback(
        Output(ResultIds.SCIENTIFIC_EXPORT_PAYLOAD, "data"),
        Output(ResultIds.SCIENTIFIC_EXPORT_STATUS, "children"),
        Input(ResultIds.SCIENTIFIC_EXPORT, "n_clicks", allow_optional=True),
        State(ResultIds.SCIENTIFIC_EXPORT_SELECTOR, "value", allow_optional=True),
        State(ResultIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_scientific_export(clicks, operation_key, session):
        if not clicks or not operation_key or not session:
            return no_update, no_update
        try:
            path = service.build_scientific_export(
                reference_from_session(session),
                str(operation_key),
            )
        except Exception as exc:
            _LOGGER.exception("Unable to build the scientific export")
            return no_update, alert(public_error_message(exc), level="error")
        return (
            dcc.send_file(path, filename=path.name),
            alert(f"Prepared scientific export {path.name}.", level="success"),
        )
