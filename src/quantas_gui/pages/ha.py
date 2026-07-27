"""Harmonic thermodynamics page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = "/ha"
NAME = "HA"
TITLE = "Harmonic thermodynamics · Quantas GUI"
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow="Harmonic thermodynamics",
        title="Harmonic thermodynamics",
        summary="Temperature-dependent vibrational thermodynamics at fixed volume.",
        next_step=(
            "The page will expose validated inputs, temperature ranges, "
            "tables and interactive thermodynamic curves."
        ),
    )
