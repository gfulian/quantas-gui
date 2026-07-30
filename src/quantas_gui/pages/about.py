"""About Quantas GUI page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_diagnostic
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/about"
NAME = "About"
TITLE = "About Quantas GUI · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return project information and the live backend diagnostic."""
    return html.Div(
        [
            html.Section(
                [
                    html.Div("Project information", className="q-eyebrow"),
                    html.H1("About Quantas GUI"),
                    html.P(
                        "Quantas GUI is an independent Dash and Plotly frontend for the "
                        "validated Quantas scientific library. Scientific operations use "
                        "only the public quantas.api lifecycle contract."
                    ),
                ],
                className="q-page-intro",
            ),
            backend_diagnostic(backend),
        ],
        className="q-content",
    )
