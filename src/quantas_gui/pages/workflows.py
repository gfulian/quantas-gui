"""Workflow catalogue page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/workflows"
NAME = "Workflows"
TITLE = "Workflow catalogue · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="Workflow catalogue unavailable",
            title="Workflows are disabled",
            summary=(
                "Scientific input generation and execution require the validated Quantas "
                "public lifecycle API."
            ),
        )
    return development_page(
        eyebrow="Scientific workflows",
        title="Workflow catalogue",
        summary=(
            "Each scientific page will keep its own methods and options while sharing the "
            "same application shell, job lifecycle, tables, and Plotly controls."
        ),
        next_step=(
            "The catalogue will be populated from quantas.api.registry, but each workflow "
            "form will remain scientifically designed rather than mechanically generated."
        ),
    )
