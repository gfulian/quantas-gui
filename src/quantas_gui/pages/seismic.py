"""SEISMIC page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/seismic"
NAME = "SEISMIC"
TITLE = "SEISMIC · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="SEISMIC workflow unavailable",
            title="SEISMIC is disabled",
            summary=(
                "The workflow requires a compatible Quantas backend before scientific "
                "operations can be used."
            ),
        )
    return development_page(
        eyebrow="Christoffel analysis",
        title="SEISMIC",
        summary=(
            "Phase and group velocity, polarization tracking, anisotropy, caustics and "
            "spherical fields."
        ),
        next_step=(
            "This page will be the principal proving ground for interactive Plotly 3D renderers."
        ),
    )
