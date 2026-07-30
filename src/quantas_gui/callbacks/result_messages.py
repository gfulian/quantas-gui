"""Stored warning and event filtering callbacks."""

from __future__ import annotations

import logging

import dash
from dash import Input, Output, State, no_update

from quantas_gui.callbacks.result_helpers import reference_from_session
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.components.results import empty_result_section, message_timeline
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.services.results import ResultExplorerService

_LOGGER = logging.getLogger(__name__)


def register_result_message_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register message-level and text filtering."""

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
            overview = service.inspect(reference_from_session(session))
        except Exception as exc:
            _LOGGER.exception("Unable to load stored result messages")
            return empty_result_section("Unable to load messages", public_error_message(exc))
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
