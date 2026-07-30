"""Equation of state page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/eos"
NAME = "EOS"
TITLE = "Equation of state · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="EOS workflow unavailable",
            title="Equation-of-state analysis is disabled",
            summary=(
                "EOS archive inspection and session operations require a compatible "
                "Quantas backend."
            ),
        )
    return development_page(
        eyebrow="Equation-of-state analysis",
        title="Equation of state",
        summary=(
            "PV, VT and PVT models, weighted fitting, diagnostics, comparison and "
            "persistent fit sessions."
        ),
        next_step=(
            "EOS will use its own session-oriented page instead of being forced into the "
            "standard one-shot workflow layout."
        ),
    )
