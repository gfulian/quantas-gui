"""Workflow catalogue page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = "/workflows"
NAME = "Workflows"
TITLE = "Workflow catalogue · Quantas GUI"
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow="Scientific workflows",
        title="Workflow catalogue",
        summary=(
            "Each scientific page will keep its own methods and options while "
            "sharing the same application shell, job lifecycle, tables, and "
            "Plotly controls."
        ),
        next_step=(
            "The catalogue will be populated from quantas.api.registry, but "
            "each workflow form will remain scientifically designed rather "
            "than mechanically generated."
        ),
    )
