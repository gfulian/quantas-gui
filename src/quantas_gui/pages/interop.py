"""Interoperability page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = "/interop"
NAME = "Interoperability"
TITLE = "Interoperability · Quantas GUI"
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow="Typed scientific transfers",
        title="Interoperability",
        summary=(
            "Move compatible Quantas results between QHA, thermoelasticity, "
            "and SEISMIC without exporting and reparsing accidental text "
            "formats."
        ),
        next_step=(
            "The first implemented transfer will open a thermoelastic P–T "
            "point directly as a SEISMIC calculation request."
        ),
    )
