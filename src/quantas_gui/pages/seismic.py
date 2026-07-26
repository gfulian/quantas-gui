"""SEISMIC page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = '/seismic'
NAME = 'SEISMIC'
TITLE = 'SEISMIC · Quantas GUI'
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow='Christoffel analysis',
        title='SEISMIC',
        summary='Phase and group velocity, polarization tracking, anisotropy, caustics and spherical fields.',
        next_step='This page will be the principal proving ground for interactive Plotly 3D renderers.',
    )
