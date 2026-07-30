"""Thermoelasticity page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/thermoelasticity"
NAME = "Thermoelasticity"
TITLE = "Thermoelasticity · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="Thermoelastic workflow unavailable",
            title="Thermoelasticity is disabled",
            summary=(
                "The workflow requires a compatible Quantas backend before scientific "
                "operations can be used."
            ),
        )
    return development_page(
        eyebrow="Quasi-static P–T elasticity",
        title="Thermoelasticity",
        summary=(
            "Calibrate elastic tensors against volume, evaluate P–T grids, and follow "
            "geothermobarometric profiles."
        ),
        next_step=(
            "The page will explicitly separate calibration, analysis, profiles, and "
            "transfer to SEISMIC."
        ),
    )
