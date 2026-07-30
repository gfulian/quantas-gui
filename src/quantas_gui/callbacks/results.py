"""Registration facade for the modular Results Explorer callbacks."""

from __future__ import annotations

import dash

from quantas_gui.callbacks.result_downloads import register_result_download_callbacks
from quantas_gui.callbacks.result_messages import register_result_message_callbacks
from quantas_gui.callbacks.result_plots import register_result_plot_callbacks
from quantas_gui.callbacks.result_session import register_result_session_callbacks
from quantas_gui.callbacks.result_tables import register_result_table_callbacks
from quantas_gui.callbacks.result_tabs import register_result_tab_callbacks
from quantas_gui.services.results import ResultExplorerService


def register_result_callbacks(
    app: dash.Dash,
    service: ResultExplorerService,
) -> None:
    """Register the complete Result Explorer callback surface."""
    register_result_session_callbacks(app, service)
    register_result_tab_callbacks(app, service)
    register_result_table_callbacks(app, service)
    register_result_plot_callbacks(app, service)
    register_result_message_callbacks(app, service)
    register_result_download_callbacks(app, service)
