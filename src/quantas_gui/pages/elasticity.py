"""Elasticity page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/elasticity"
NAME = "Elasticity"
TITLE = "Elasticity · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="Elasticity workflow unavailable",
            title="Elasticity is disabled",
            summary=(
                "The workflow requires a compatible Quantas backend before inputs, "
                "calculations, reports, or plots can be used."
            ),
        )
    return development_page(
        eyebrow="Second-order elasticity",
        title="Elasticity",
        summary=(
            "Mechanical stability, VRH averages, tensor rotations, and exact directional "
            "properties."
        ),
        next_step=(
            "After the Results Explorer, Elasticity will become the first complete "
            "executable GUI workflow."
        ),
    )
