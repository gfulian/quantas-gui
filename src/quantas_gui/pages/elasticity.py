"""Executable Elasticity workflow page."""

from __future__ import annotations

from dash import dcc, html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.components.feedback import message_banner
from quantas_gui.forms.renderer import render_form
from quantas_gui.services.backend_info import BackendCompatibility
from quantas_gui.services.backends import ExecutionBackendDescriptor
from quantas_gui.workflows.elasticity.ids import ElasticityIds
from quantas_gui.workflows.elasticity.presentation import activity_tabs
from quantas_gui.workflows.elasticity.schema import elasticity_form

PATH = "/elasticity"
NAME = "Elasticity"
TITLE = "Elasticity · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True
USES_EXECUTION_STATUS = True

_SCHEMA = elasticity_form()


def layout(
    *,
    backend: BackendCompatibility,
    execution: ExecutionBackendDescriptor,
) -> html.Div:
    """Return the Elasticity workflow or a degraded-mode diagnostic."""
    if not backend.workflow_ready("elasticity"):
        return backend_required_page(
            backend,
            eyebrow="Elasticity workflow unavailable",
            title="Elasticity is disabled",
            summary=(
                "The workflow requires the complete public Quantas Elasticity lifecycle "
                "before inputs, calculations, reports, or plots can be used."
            ),
        )
    if not execution.available:
        return html.Div(
            [
                html.Section(
                    [
                        html.Div("Second-order elasticity", className="q-eyebrow"),
                        html.H1("Elasticity"),
                    ],
                    className="q-page-intro",
                ),
                message_banner(
                    title="Elasticity execution is unavailable",
                    message=execution.detail,
                    level="warning",
                ),
            ],
            className="q-content q-workflow-page q-elasticity-page",
        )

    return html.Div(
        [
            dcc.Store(id=ElasticityIds.SOURCE, storage_type="session"),
            dcc.Store(id=ElasticityIds.SESSION, storage_type="session"),
            dcc.Store(id=ElasticityIds.EVENTS, storage_type="session", data=[]),
            dcc.Interval(
                id=ElasticityIds.POLL,
                interval=750,
                n_intervals=0,
                disabled=True,
            ),
            dcc.Download(id=ElasticityIds.DOWNLOAD_HDF5_PAYLOAD),
            dcc.Download(id=ElasticityIds.DOWNLOAD_REPORT_PAYLOAD),
            dcc.Download(id=ElasticityIds.DOWNLOAD_DIAGNOSTIC_PAYLOAD),
            html.Section(
                [
                    html.Div("Second-order elasticity", className="q-eyebrow"),
                    html.H1("Elasticity"),
                    html.P(
                        "Calculate mechanical stability, Voigt–Reuss–Hill averages, "
                        "directional elastic properties, and optional physical tensor "
                        "transformations through the public Quantas API."
                    ),
                ],
                className="q-page-intro",
            ),
            html.Div(id=ElasticityIds.IMPORT_STATUS, className="q-workflow-import-status"),
            html.Div(
                render_form(_SCHEMA),
                id=ElasticityIds.FORM_HOST,
                className="q-workflow-form-host",
            ),
            html.Section(
                id=ElasticityIds.RUNTIME,
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
                    html.Div(id=ElasticityIds.ACTIVITY_OUTPUT),
                ],
                id=ElasticityIds.ACTIVITY,
                className="q-workflow-activity is-hidden",
            ),
            html.Section(
                id=ElasticityIds.SUMMARY,
                className="q-workflow-summary is-hidden",
                **{"aria-live": "polite"},
            ),
        ],
        className="q-content q-workflow-page q-elasticity-page",
    )


__all__ = ["layout"]
