"""Developer-facing reusable component gallery."""

from __future__ import annotations

from typing import Any

from dash import Input, Output, State, callback, html

from quantas_gui.components.feedback import (
    log_viewer,
    message_banner,
    progress_panel,
    structured_result_panel,
    validation_summary,
)
from quantas_gui.forms.catalog import ui_kit_form
from quantas_gui.forms.ids import FormIds
from quantas_gui.forms.renderer import render_form
from quantas_gui.forms.schema import FileUploadField
from quantas_gui.forms.validation import validate_form
from quantas_gui.forms.values import normalize_component_value, value_component_id, value_property

PATH = "/ui-kit"
NAME = "UI Kit"
TITLE = "Scientific UI Kit · Quantas GUI"
ORDER = None

_SCHEMA = ui_kit_form()
_FIELDS = tuple(field for field in _SCHEMA.fields if not isinstance(field, FileUploadField))
_ERROR_OUTPUTS = tuple(
    Output(FormIds.error(_SCHEMA.key, field.key), "children") for field in _FIELDS
)
_VALUE_STATES = tuple(
    State(value_component_id(_SCHEMA.key, field), value_property(field)) for field in _FIELDS
)


def layout() -> html.Div:
    """Return the component-library page."""
    return html.Div(
        [
            html.Section(
                [
                    html.Div("Reusable interface foundation", className="q-eyebrow"),
                    html.H1("Scientific UI Kit"),
                    html.P(
                        "A declarative component system derived from the real Quantas CLI and API "
                        "option space. This page is a development gallery, not a "
                        "scientific workflow."
                    ),
                ],
                className="q-page-intro",
            ),
            html.Section(
                [
                    html.Div(
                        [
                            html.H2("Runtime feedback"),
                            html.P(
                                "The same components will present Quantas events, validation, "
                                "progress, "
                                "warnings, errors, and structured results."
                            ),
                        ],
                        className="q-section-heading",
                    ),
                    html.Div(
                        [
                            message_banner(
                                title="Input accepted",
                                message="The file is structurally valid and ready for inspection.",
                                level="info",
                            ),
                            message_banner(
                                title="Extrapolation warning",
                                message=(
                                    "Requested P–T points extend beyond the calibrated "
                                    "elastic-volume range."
                                ),
                                level="warning",
                                details="policy=warn; out_of_range_points=14",
                            ),
                            message_banner(
                                title="Calculation stopped",
                                message="The stiffness matrix is not positive definite.",
                                level="error",
                            ),
                        ],
                        className="q-feedback-grid",
                    ),
                    html.Div(
                        [
                            progress_panel(
                                title="Sampling acoustic directions",
                                progress=0.63,
                                current=11403,
                                total=18091,
                                message="Computing group velocities and enhancement factors…",
                            ),
                            log_viewer(
                                [
                                    "[INFO] Reading normalized input",
                                    "[INFO] Crystal system: trigonal",
                                    "[PROGRESS] Sampling directions 11403 / 18091",
                                    "[WARNING] 3 near-degenerate shear-mode points",
                                ]
                            ),
                            structured_result_panel(
                                title="Current state",
                                data={
                                    "Pressure": "2.50 GPa",
                                    "Temperature": "673.15 K",
                                    "Volume": "217.481 Å³",
                                },
                            ),
                        ],
                        className="q-feedback-runtime-grid",
                    ),
                ],
                className="q-ui-kit-section",
            ),
            html.Section(
                [
                    html.Div(
                        [
                            html.H2("Form composition"),
                            html.P(
                                "Each section and field is described by passive dataclasses, "
                                "rendered by one shared Dash adapter, and validated before "
                                "API dataclasses are built."
                            ),
                        ],
                        className="q-section-heading",
                    ),
                    render_form(_SCHEMA),
                ],
                className="q-ui-kit-section",
            ),
        ],
        className="q-content q-ui-kit",
    )


@callback(
    Output(FormIds.summary(_SCHEMA.key), "children"),
    *_ERROR_OUTPUTS,
    Input(FormIds.submit(_SCHEMA.key), "n_clicks"),
    *_VALUE_STATES,
    prevent_initial_call=True,
)
def validate_gallery(
    clicks: int | None,
    *raw_values: Any,
) -> tuple[Any, ...]:
    """Validate the gallery form and display reusable error components."""
    del clicks
    values = {
        field.key: normalize_component_value(field, raw)
        for field, raw in zip(_FIELDS, raw_values, strict=True)
    }
    result = validate_form(_SCHEMA, values)
    summary = validation_summary(result.issues)
    errors: list[Any] = []
    for field in _FIELDS:
        issues = result.for_field(field.key)
        errors.append(" ".join(issue.message for issue in issues))
    if result.valid:
        summary = message_banner(
            title="Form values are structurally valid",
            message=(
                "A real workflow would now construct the public Quantas API input and options "
                "dataclasses, which remain the final validation boundary."
            ),
            level="result",
        )
    return summary, *errors


@callback(
    Output(f"q-form-{_SCHEMA.key}", "children"),
    Input(FormIds.reset(_SCHEMA.key), "n_clicks"),
    prevent_initial_call=True,
)
def reset_gallery(clicks: int | None) -> Any:
    """Restore the gallery form from its immutable schema defaults."""
    del clicks
    return render_form(_SCHEMA).children


__all__ = ["layout"]
