"""Quasi-harmonic approximation page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = "/qha"
NAME = "QHA"
TITLE = "Quasi-harmonic approximation · Quantas GUI"
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow="Quasi-harmonic approximation",
        title="Quasi-harmonic approximation",
        summary=(
            "Equilibrium volume, thermal expansion, heat capacities, and "
            "free-energy minimization over pressure and temperature."
        ),
        next_step=(
            "The GUI will preserve inspection and diagnostic stages instead "
            "of hiding fitting and minimization choices."
        ),
    )
