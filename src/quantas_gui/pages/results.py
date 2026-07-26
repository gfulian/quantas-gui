"""Native HDF5 Results Explorer page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.results import explorer_layout

PATH = "/results"
NAME = "Results"
TITLE = "Results Explorer · Quantas GUI"
ORDER = 1


def layout() -> html.Div:
    """Return the complete lazy Results Explorer page."""
    return explorer_layout()
