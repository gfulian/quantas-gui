"""Harmonic thermodynamics page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/ha"
NAME = "HA"
TITLE = "Harmonic thermodynamics · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="HA workflow unavailable",
            title="Harmonic analysis is disabled",
            summary=(
                "The workflow requires a compatible Quantas backend before scientific "
                "operations can be used."
            ),
        )
    return development_page(
        eyebrow="Harmonic thermodynamics",
        title="Harmonic thermodynamics",
        summary="Temperature-dependent vibrational thermodynamics at fixed volume.",
        next_step=(
            "The page will expose validated inputs, temperature ranges, tables and "
            "interactive thermodynamic curves."
        ),
    )
