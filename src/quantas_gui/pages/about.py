"""About Quantas GUI page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = "/about"
NAME = "About"
TITLE = "About Quantas GUI · Quantas GUI"
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow="Project information",
        title="About Quantas GUI",
        summary="A modern graphical interface to the validated Quantas Python library.",
        next_step=(
            "Project, version, citation, license, and backend compatibility "
            "information will live here."
        ),
    )
