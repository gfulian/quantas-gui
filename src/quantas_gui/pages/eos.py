"""Equation of state page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = "/eos"
NAME = "EOS"
TITLE = "Equation of state · Quantas GUI"
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow="Equation-of-state analysis",
        title="Equation of state",
        summary=(
            "PV, VT and PVT models, weighted fitting, diagnostics, "
            "comparison and persistent fit sessions."
        ),
        next_step=(
            "EOS will use its own session-oriented page instead of being "
            "forced into the standard one-shot workflow layout."
        ),
    )
