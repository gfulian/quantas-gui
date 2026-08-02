"""Scientific workflow catalogue page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import dash
from dash import dcc, html

from quantas_gui.components.backend import backend_required_page
from quantas_gui.services.backend_info import BackendCompatibility

PATH = "/workflows"
NAME = "Workflows"
TITLE = "Workflow catalogue · Quantas GUI"
ORDER = None
USES_BACKEND_STATUS = True

WorkflowState = Literal["available", "next", "planned"]


@dataclass(frozen=True, slots=True)
class WorkflowCardSpec:
    """Stable presentation metadata for one scientific workflow."""

    slug: str
    title: str
    kicker: str
    summary: str
    input_summary: str
    result_summary: str
    milestone: str
    state: WorkflowState
    api_module: str


WORKFLOWS = (
    WorkflowCardSpec(
        slug="elasticity",
        title="Elasticity",
        kicker="Elastic tensors",
        summary=(
            "Evaluate stability, compliance, Voigt–Reuss–Hill averages and optional "
            "two- and three-dimensional directional properties."
        ),
        input_summary="Job name and elastic stiffness tensor in GPa",
        result_summary="Native Quantas Elasticity HDF5",
        milestone="0.3",
        state="available",
        api_module="elasticity",
    ),
    WorkflowCardSpec(
        slug="seismic",
        title="SEISMIC",
        kicker="Wave propagation",
        summary=(
            "Solve the Christoffel equation for phase and group velocities, polarization, "
            "anisotropy, degeneracies and enhancement."
        ),
        input_summary="Elastic stiffness tensor in GPa and density",
        result_summary="Native Quantas SEISMIC HDF5",
        milestone="0.4",
        state="available",
        api_module="seismic",
    ),
    WorkflowCardSpec(
        slug="ha",
        title="Harmonic thermodynamics",
        kicker="Fixed-volume properties",
        summary=(
            "Calculate vibrational thermodynamic functions over temperature from compatible "
            "phonon data."
        ),
        input_summary="Harmonic phonon and structural data",
        result_summary="Native Quantas HA HDF5",
        milestone="0.5",
        state="next",
        api_module="ha",
    ),
    WorkflowCardSpec(
        slug="qha",
        title="Quasi-harmonic approximation",
        kicker="Pressure–temperature properties",
        summary=(
            "Determine equilibrium volumes and thermodynamic properties across temperature "
            "and pressure."
        ),
        input_summary="Volume-dependent phonon and static-energy data",
        result_summary="Native Quantas QHA HDF5",
        milestone="0.5",
        state="next",
        api_module="qha",
    ),
    WorkflowCardSpec(
        slug="thermoelasticity",
        title="Thermoelasticity",
        kicker="Quasi-static P–T analysis",
        summary=(
            "Combine volume-dependent elastic tensors with QHA results for point, grid and "
            "profile calculations."
        ),
        input_summary="Elastic-volume series and compatible QHA result",
        result_summary="Native Quantas Thermoelasticity HDF5",
        milestone="0.6",
        state="planned",
        api_module="thermoelasticity",
    ),
    WorkflowCardSpec(
        slug="eos",
        title="Equation of state",
        kicker="Persistent fitting sessions",
        summary=(
            "Fit and compare PV, VT and PVT models through a dedicated persistent session "
            "rather than a generic one-shot calculation."
        ),
        input_summary="PV, VT or PVT datasets",
        result_summary="Native Quantas EOS archive",
        milestone="0.7",
        state="planned",
        api_module="eos",
    ),
)


def layout(*, backend: BackendCompatibility) -> html.Div:
    """Return the operational workflow catalogue or a degraded-mode diagnostic."""
    if not backend.ready:
        return backend_required_page(
            backend,
            eyebrow="Workflow catalogue unavailable",
            title="Workflows are disabled",
            summary=(
                "Scientific input generation and execution require the validated Quantas "
                "public lifecycle API."
            ),
        )

    return html.Div(
        [
            html.Section(
                [
                    html.Div("Scientific workflows", className="q-eyebrow"),
                    html.H1("Choose an analysis"),
                    html.P(
                        "Each workflow uses the public Quantas API and produces a native "
                        "scientific result that can be opened in the shared Result Explorer. "
                        "Backend readiness and GUI availability are reported separately."
                    ),
                ],
                className="q-page-intro",
            ),
            html.Div(
                [_workflow_card(spec, backend=backend) for spec in WORKFLOWS],
                className="q-workflow-catalogue-grid",
            ),
            html.Section(
                [
                    html.Div("Shared lifecycle", className="q-eyebrow"),
                    html.H2("One application pattern, module-specific science"),
                    html.P(
                        "Executable calculators share controlled uploads, background jobs, "
                        "progress, warnings, native HDF5 publication and result handoff. "
                        "Their scientific fields and options remain explicitly designed for "
                        "each Quantas module."
                    ),
                ],
                className="q-panel q-workflow-catalogue-note",
            ),
        ],
        className="q-content q-workflow-catalogue",
    )


def _workflow_card(
    spec: WorkflowCardSpec,
    *,
    backend: BackendCompatibility,
) -> html.Article:
    api_ready, api_label, api_detail = _api_state(spec, backend=backend)
    state_label, state_class = _gui_state(spec.state, milestone=spec.milestone)
    can_start = spec.state == "available" and api_ready

    action: Any
    if can_start:
        action = dcc.Link(
            "Start workflow",
            href=dash.get_relative_path(f"/{spec.slug}"),
            className="q-button q-button--primary",
        )
    elif spec.state == "available":
        action = html.Span(
            "Workflow unavailable",
            className="q-button is-disabled",
            title=api_detail,
            **{"aria-disabled": "true"},
        )
    elif spec.state == "next":
        action = html.Span("Next milestone", className="q-button is-disabled")
    else:
        action = html.Span("Planned", className="q-button is-disabled")

    return html.Article(
        [
            html.Div(
                [
                    html.Div(spec.kicker, className="q-workflow-catalogue-kicker"),
                    html.Div(
                        [
                            html.Span(
                                state_label,
                                className=f"q-status-pill {state_class}",
                            ),
                            html.Span(
                                api_label,
                                className=(
                                    "q-status-pill is-success"
                                    if api_ready
                                    else "q-status-pill is-warning"
                                ),
                                title=api_detail,
                            ),
                        ],
                        className="q-workflow-catalogue-statuses",
                    ),
                ],
                className="q-workflow-catalogue-header",
            ),
            html.H2(spec.title),
            html.P(spec.summary, className="q-workflow-catalogue-summary"),
            html.Dl(
                [
                    html.Div([html.Dt("Input"), html.Dd(spec.input_summary)]),
                    html.Div([html.Dt("Persistence"), html.Dd(spec.result_summary)]),
                ],
                className="q-workflow-catalogue-meta",
            ),
            html.Div(
                [
                    html.Span(f"Milestone {spec.milestone}", className="q-workflow-milestone"),
                    action,
                ],
                className="q-workflow-catalogue-footer",
            ),
        ],
        className=f"q-panel q-workflow-catalogue-card is-{spec.state}",
    )


def _api_state(
    spec: WorkflowCardSpec,
    *,
    backend: BackendCompatibility,
) -> tuple[bool, str, str]:
    if spec.api_module == "eos":
        return (
            backend.ready,
            "API ready" if backend.ready else "API unavailable",
            "EOS uses the public archive and fitting-session contract.",
        )

    missing = backend.workflow_missing_for(spec.api_module)
    if not missing:
        return True, "API ready", "The public Quantas workflow lifecycle is available."
    return (
        False,
        "API incomplete",
        "Missing public operations: " + ", ".join(missing) + ".",
    )


def _gui_state(state: WorkflowState, *, milestone: str) -> tuple[str, str]:
    if state == "available":
        return "Available", "is-success"
    if state == "next":
        return f"Next · {milestone}", "is-info"
    return "Planned", "is-planned"
