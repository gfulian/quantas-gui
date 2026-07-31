"""Active-result lifecycle callbacks shared by uploads and future workflows."""

from __future__ import annotations

import logging
from contextlib import suppress

import dash
from dash import Input, Output, State, ctx, no_update

from quantas_gui.callbacks.result_helpers import (
    reference_from_session,
    result_session_data,
    summary_from_session,
)
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.components.results import alert, result_header
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.services.result_backend import ResultBackendError
from quantas_gui.services.results import ResultExplorerService, ResultUploadError

_LOGGER = logging.getLogger(__name__)


def register_result_session_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register upload, close, and active-result shell callbacks."""

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
                    service.close(reference_from_session(session))
            return None, alert("Result closed.", level="success")

        contents = compact_contents if triggered == ResultIds.UPLOAD_COMPACT else upload_contents
        filename = compact_filename if triggered == ResultIds.UPLOAD_COMPACT else upload_filename
        if not contents or not filename:
            return no_update, no_update

        try:
            reference, overview = service.ingest_upload(filename=filename, contents=contents)
        except (ResultUploadError, ResultBackendError, ValueError, OSError) as exc:
            _LOGGER.warning("Native result upload rejected: %s", public_error_message(exc))
            return no_update, alert(public_error_message(exc), level="error")
        except Exception as exc:
            _LOGGER.exception("Unexpected failure while opening a native result")
            return no_update, alert(
                f"Unable to open this native result: {public_error_message(exc)}",
                level="error",
            )

        if session:
            with suppress(Exception):
                service.close(reference_from_session(session))

        return result_session_data(reference, overview), alert(
            f"Opened {reference.filename} as {overview.summary.module_title}.",
            level="success",
        )

    @app.callback(
        Output(ResultIds.UPLOAD_PANEL, "className"),
        Output(ResultIds.WORKSPACE, "className"),
        Output(ResultIds.HEADER, "children"),
        Input(ResultIds.SESSION, "data"),
        Input("q-location", "pathname"),
        Input(ResultIds.HYDRATE, "n_intervals", allow_optional=True),
    )
    def render_session_shell(session, pathname, hydrate_count):
        del pathname, hydrate_count
        if not session:
            return "q-panel q-result-open-panel", "q-result-workspace is-hidden", None
        return (
            "q-panel q-result-open-panel is-hidden",
            "q-result-workspace",
            result_header(reference_from_session(session), summary_from_session(session)),
        )
