"""Executable SEISMIC workflow page."""

from __future__ import annotations

from dash import dcc, html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.feedback import message_banner
from quantas_gui.forms.renderer import render_form
from quantas_gui.services.backend_info import BackendCompatibility
from quantas_gui.services.backends import ExecutionBackendDescriptor
from quantas_gui.workflows.seismic.ids import SeismicIds
from quantas_gui.workflows.seismic.presentation import activity_tabs
from quantas_gui.workflows.seismic.schema import seismic_form

PATH = "/seismic"
NAME = "SEISMIC"
TITLE = "SEISMIC · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True
USES_EXECUTION_STATUS = True

_SCHEMA = seismic_form()


def layout(
    *,
    backend: BackendCompatibility,
    execution: ExecutionBackendDescriptor,
) -> html.Div:
    """Return the SEISMIC workflow or a degraded-mode diagnostic."""
    if not backend.workflow_ready("seismic"):
        return backend_required_page(
            backend,
            eyebrow="SEISMIC workflow unavailable",
            title="SEISMIC is disabled",
            summary=(
                "The workflow requires the complete public Quantas SEISMIC lifecycle, "
                "including controlled CRYSTAL and VASP input generation."
            ),
        )
    if not execution.available:
        return html.Div(
            [
                html.Section(
                    [
                        html.Div("Christoffel analysis", className="q-eyebrow"),
                        html.H1("SEISMIC"),
                    ],
                    className="q-page-intro",
                ),
                message_banner(
                    title="SEISMIC execution is unavailable",
                    message=execution.detail,
                    level="warning",
                ),
            ],
            className="q-content q-workflow-page q-seismic-page",
        )

    return html.Div(
        [
            dcc.Store(id=SeismicIds.SOURCE, storage_type="session"),
            dcc.Store(id=SeismicIds.SESSION, storage_type="session"),
            dcc.Store(id=SeismicIds.EVENTS, storage_type="session", data=[]),
            dcc.Interval(
                id=SeismicIds.POLL,
                interval=750,
                n_intervals=0,
                disabled=True,
            ),
            dcc.Download(id=SeismicIds.DOWNLOAD_HDF5_PAYLOAD),
            dcc.Download(id=SeismicIds.DOWNLOAD_REPORT_PAYLOAD),
            dcc.Download(id=SeismicIds.DOWNLOAD_CSV_PAYLOAD),
            dcc.Download(id=SeismicIds.DOWNLOAD_DIAGNOSTIC_PAYLOAD),
            html.Section(
                [
                    html.Div("Christoffel analysis", className="q-eyebrow"),
                    html.H1("SEISMIC"),
                    html.P(
                        "Calculate phase and group velocities, polarizations, anisotropy, "
                        "degeneracies, enhancement and caustic diagnostics through the public "
                        "Quantas API."
                    ),
                ],
                className="q-page-intro",
            ),
            html.Div(id=SeismicIds.IMPORT_STATUS, className="q-workflow-import-status"),
            html.Div(
                render_form(_SCHEMA),
                id=SeismicIds.FORM_HOST,
                className="q-workflow-form-host",
            ),
            html.Section(
                id=SeismicIds.RUNTIME,
                className="q-workflow-runtime is-hidden",
                **{"aria-live": "polite"},
            ),
            html.Section(
                [
                    html.Div(
                        [
                            html.H2("Calculation activity"),
                            html.P("Ordered frontend-neutral events from the worker and Quantas."),
                        ],
                        className="q-section-heading",
                    ),
                    activity_tabs(),
                    html.Div(id=SeismicIds.ACTIVITY_OUTPUT),
                ],
                id=SeismicIds.ACTIVITY,
                className="q-workflow-activity is-hidden",
            ),
            html.Section(
                id=SeismicIds.SUMMARY,
                className="q-workflow-summary is-hidden",
                **{"aria-live": "polite"},
            ),
        ],
        className="q-content q-workflow-page q-seismic-page",
    )


__all__ = ["layout"]
