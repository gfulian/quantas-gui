"""Native HDF5 Results Explorer page."""

from __future__ import annotations

from dash import html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.results import explorer_layout
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/results"
NAME = "Results"
TITLE = "Results Explorer · Quantas GUI"
ORDER = 1
USES_BACKEND_STATUS = True


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the Result Explorer or an explicit degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="Native result inspection unavailable",
            title="Results Explorer is disabled",
            summary=(
                "Opening HDF5 results requires the validated Quantas public lifecycle API. "
                "No upload is decoded or written while the backend is unavailable or incompatible."
            ),
        )
    return explorer_layout()
