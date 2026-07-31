"""Top-level Results Explorer tab rendering callbacks."""

from __future__ import annotations

import logging

import dash
from dash import Input, Output

from quantas_gui.callbacks.result_helpers import reference_from_session
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.components.results import (
    data_view,
    empty_result_section,
    messages_view,
    overview_view,
    plots_view,
    tables_view,
)
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.services.results import ResultExplorerService

_LOGGER = logging.getLogger(__name__)


def register_result_tab_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register lazy top-level section construction."""

    @app.callback(
        Output(ResultIds.TAB_CONTENT, "children"),
        Input(ResultIds.TABS, "value"),
        Input(ResultIds.SESSION, "data"),
        Input(ResultIds.HYDRATE, "n_intervals", allow_optional=True),
    )
    def render_tab(tab, session, hydrate_count):
        del hydrate_count
        if not session:
            return None
        reference = reference_from_session(session)
        try:
            if tab == "tables":
                table_families = service.table_families(reference)
                selected_table_family = next(
                    (item for item in table_families if item.default),
                    table_families[0] if table_families else None,
                )
                tables = (
                    service.build_tables(reference, selected_table_family.key)
                    if selected_table_family
                    else ()
                )
                groups = tuple(service.table_group(reference, str(table.title)) for table in tables)
                return tables_view(
                    table_families,
                    exports=service.scientific_exports(reference),
                    initial_tables=tables,
                    initial_groups=groups,
                )
            if tab == "plots":
                plot_families = service.plot_families(reference)
                selected_plot_family = next(
                    (item for item in plot_families if item.default),
                    plot_families[0] if plot_families else None,
                )
                schema = (
                    service.plot_selection_schema(reference, selected_plot_family.key)
                    if selected_plot_family
                    else None
                )
                return plots_view(plot_families, initial_schema=schema)

            overview = service.inspect(reference)
            if tab == "messages":
                return messages_view(overview)
            if tab == "data":
                return data_view(overview)
            return overview_view(reference, overview)
        except Exception as exc:
            _LOGGER.exception("Unable to render the selected Result Explorer section")
            return empty_result_section("Unable to render this section", public_error_message(exc))
