"""Report-table construction and selection callbacks."""

from __future__ import annotations

import logging

import dash
from dash import Input, Output, State, no_update

from quantas_gui.callbacks.result_helpers import reference_from_session
from quantas_gui.components.renderer_controls import family_note
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.components.results import empty_result_section, rendered_tables_view
from quantas_gui.renderers.tables import table_component
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.services.results import ResultExplorerService

_LOGGER = logging.getLogger(__name__)


def register_result_table_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register lazy table-family and table-selection callbacks."""

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
        reference = reference_from_session(session)
        try:
            families = service.table_families(reference)
            selected_family = next((item for item in families if item.key == family_key), None)
            tables = service.build_tables(reference, family_key)
            groups = tuple(service.table_group(reference, str(table.title)) for table in tables)
            return (
                rendered_tables_view(tables, page_size=int(page_size or 50), groups=groups),
                family_note(selected_family),
            )
        except Exception as exc:
            _LOGGER.exception("Unable to build the selected report family")
            return (
                empty_result_section(
                    "Unable to build this report family",
                    public_error_message(exc),
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
            tables = service.build_tables(reference_from_session(session), family_key)
            return table_component(
                tables[int(selected)],
                component_id="q-result-table",
                page_size=int(page_size or 50),
            )
        except Exception as exc:
            _LOGGER.exception("Unable to render the selected report table")
            return empty_result_section(
                "Unable to render the selected table",
                public_error_message(exc),
            )
