"""Landing page for Quantas GUI."""

from __future__ import annotations

import dash
from dash import dcc, html

from quantas_gui.components.cards import ModuleCardSpec, module_card

PATH = "/"
NAME = "Home"
TITLE = "Quantas GUI"
ORDER = 0

MODULES = (
    ModuleCardSpec(
        "elasticity",
        "Elasticity",
        "Elastic tensors",
        "Stability criteria, Voigt–Reuss–Hill averages, tensor rotations, and directional elastic properties.",
        "elasticity.png",
    ),
    ModuleCardSpec(
        "seismic",
        "SEISMIC",
        "Wave propagation",
        "Christoffel analysis, phase and group velocities, polarization tracking, and directional anisotropy.",
        "seismic.png",
    ),
    ModuleCardSpec(
        "ha",
        "Harmonic thermodynamics",
        "Fixed-volume properties",
        "Vibrational energy, Helmholtz free energy, entropy, and heat capacity as functions of temperature.",
        "ha.png",
    ),
    ModuleCardSpec(
        "qha",
        "Quasi-harmonic approximation",
        "Pressure–temperature properties",
        "Equilibrium volumes, thermal expansion, heat capacities, and free-energy minimization over pressure and temperature.",
        "qha.png",
    ),
    ModuleCardSpec(
        "eos",
        "Equation of state",
        "Fitting and diagnostics",
        "PV, VT, and PVT models with uncertainty treatment, residual analysis, and model diagnostics.",
        "eos.png",
    ),
    ModuleCardSpec(
        "thermoelasticity",
        "Thermoelasticity",
        "Quasi-static P–T analysis",
        "Pressure–temperature elastic tensors, grids, geothermobarometric profiles, and transfer to SEISMIC.",
        "thermoelasticity.png",
    ),
)


def _capability(
    icon: str,
    title: str,
    subtitle: str,
    state: str,
) -> html.Div:
    return html.Div(
        [
            html.Div(icon, className="q-capability-icon"),
            html.Div([html.Strong(title), html.Small(subtitle)]),
            html.Span(state, className="q-capability-state"),
        ],
        className="q-capability",
    )


def _inspection_step(number: str, title: str, subtitle: str) -> html.Div:
    return html.Div(
        [html.Span(number), html.Div([html.Strong(title), html.Small(subtitle)])],
        className="q-flow-step",
    )


def layout() -> html.Div:
    """Return the landing-page layout."""
    return html.Div(
        [
            html.Section(
                [
                    html.Div(
                        [
                            html.Div(
                                "Quantitative analysis of solid-state properties",
                                className="q-eyebrow",
                            ),
                            html.H1(
                                [
                                    "Interactive access to ",
                                    html.Span("Quantas calculations and results."),
                                ]
                            ),
                            html.P(
                                "Quantas GUI is a Dash-based interface to the Quantas "
                                "Python library. It provides structured access to native "
                                "HDF5 results and will expose the same scientific workflows "
                                "available through the API and command line, without changing "
                                "numerical methods, units, or stored data."
                            ),
                            html.Div(
                                [
                                    dcc.Link(
                                        "Open Result Explorer",
                                        href=dash.get_relative_path("/results"),
                                        className="q-button q-button--primary",
                                    ),
                                    dcc.Link(
                                        "Review workflow structure",
                                        href=dash.get_relative_path("/workflows"),
                                        className="q-button",
                                    ),
                                ],
                                className="q-hero-actions",
                            ),
                        ],
                        className="q-hero-copy",
                    ),
                    html.Div(
                        [
                            _capability(
                                "H5",
                                "Native HDF5 results",
                                "Metadata, inputs, outputs, and diagnostics",
                                "Available",
                            ),
                            _capability(
                                "API",
                                "Shared scientific backend",
                                "Library, CLI, and GUI use the same calculators",
                                "Required",
                            ),
                            _capability(
                                "↔",
                                "Explicit interoperability",
                                "Typed transfer between compatible analyses",
                                "Planned",
                            ),
                        ],
                        className="q-hero-panel",
                    ),
                ],
                className="q-hero",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Scientific modules"),
                            html.P(
                                "Module pages will combine shared interface components with "
                                "workflow-specific scientific options and validation."
                            ),
                        ]
                    ),
                    dcc.Link(
                        "View workflow map →",
                        href=dash.get_relative_path("/workflows"),
                        className="q-button",
                    ),
                ],
                className="q-section-heading",
            ),
            html.Div([module_card(spec) for spec in MODULES], className="q-module-grid"),
            html.Div(
                [
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.H3("Result Explorer"),
                                    dcc.Link(
                                        "Open Explorer →",
                                        href=dash.get_relative_path("/results"),
                                    ),
                                ],
                                className="q-panel-header",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Inspect native Quantas results without rerunning a "
                                        "calculation. Module-aware adapters expose provenance, "
                                        "tables, persistent messages, and interactive Plotly "
                                        "figures through a common interface."
                                    ),
                                    html.Div(
                                        [
                                            _inspection_step(
                                                "1", "Open HDF5", "Identify module and schema"
                                            ),
                                            _inspection_step(
                                                "2",
                                                "Inspect results",
                                                "Metadata, reports, and diagnostics",
                                            ),
                                            _inspection_step(
                                                "3",
                                                "Render interactively",
                                                "Tables and module-specific Plotly figures",
                                            ),
                                        ],
                                        className="q-flow q-result-explorer-flow",
                                    ),
                                ],
                                className="q-home-panel-body",
                            ),
                        ],
                        className="q-panel",
                    ),
                    html.Section(
                        [
                            html.H3("Interoperability path"),
                            html.P(
                                "Compatible results can be transferred through explicit API "
                                "contracts while preserving the scientific choices made at "
                                "each stage."
                            ),
                            html.Div(
                                [
                                    _inspection_step(
                                        "1", "QHA", "Thermodynamic pressure–temperature context"
                                    ),
                                    _inspection_step(
                                        "2",
                                        "Thermoelasticity",
                                        "Isothermal or adiabatic elastic tensors",
                                    ),
                                    _inspection_step(
                                        "3",
                                        "SEISMIC",
                                        "Directional wave propagation",
                                    ),
                                ],
                                className="q-flow",
                            ),
                        ],
                        className="q-panel q-workflow-card",
                    ),
                ],
                className="q-lower-grid",
            ),
        ],
        className="q-content",
    )
