"""Interoperability page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.placeholders import development_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/interop"
NAME = "Interoperability"
TITLE = "Interoperability · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the page layout or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="Interoperability unavailable",
            title="Interoperability is disabled",
            summary="Typed scientific transfers require compatible public Quantas operations.",
        )
    return development_page(
        eyebrow="Typed scientific transfers",
        title="Interoperability",
        summary=(
            "Move compatible Quantas results between QHA, thermoelasticity, and SEISMIC "
            "without exporting and reparsing accidental text formats."
        ),
        next_step=(
            "The first implemented transfer will open a thermoelastic P–T point directly "
            "as a SEISMIC calculation request."
        ),
    )
