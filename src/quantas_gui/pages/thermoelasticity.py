"""Thermoelasticity page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.placeholders import development_page

PATH = '/thermoelasticity'
NAME = 'Thermoelasticity'
TITLE = 'Thermoelasticity · Quantas GUI'
ORDER = None


def layout() -> html.Div:
    """Return the page layout."""
    return development_page(
        eyebrow='Quasi-static P–T elasticity',
        title='Thermoelasticity',
        summary='Calibrate elastic tensors against volume, evaluate P–T grids and follow geothermobarometric profiles.',
        next_step='The page will explicitly separate calibration, analysis, profiles and transfer to SEISMIC.',
    )
