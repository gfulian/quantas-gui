"""Elasticity page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = '/elasticity'
NAME = 'Elasticity'
TITLE = 'Elasticity · Quantas GUI'
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow='Second-order elasticity',
        title='Elasticity',
        summary='Mechanical stability, VRH averages, tensor rotations and exact directional properties.',
        next_step='After the Results Explorer, Elasticity will become the first complete executable GUI workflow.',
    )
