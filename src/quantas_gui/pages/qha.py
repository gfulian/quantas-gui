"""Quasi-harmonic approximation page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/qha"
NAME = "QHA"
TITLE = "Quasi-harmonic approximation · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="QHA workflow unavailable",
            title="Quasi-harmonic analysis is disabled",
            summary=(
                "The workflow requires a compatible Quantas backend before scientific "
                "operations can be used."
            ),
        )
    return development_page(
        eyebrow="Quasi-harmonic approximation",
        title="Quasi-harmonic approximation",
        summary=(
            "Equilibrium volume, thermal expansion, heat capacities, and free-energy "
            "minimization over pressure and temperature."
        ),
        next_step=(
            "The GUI will preserve inspection and diagnostic stages instead of hiding "
            "fitting and minimization choices."
        ),
    )
