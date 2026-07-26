"""Reusable presentation components for application preferences."""

from __future__ import annotations

from collections.abc import Sequence

import dash
from dash import dcc, html


Option = tuple[str, str, str]


def preference_group(
    *,
    title: str,
    description: str,
    control: object,
    note: str | None = None,
) -> html.Section:
    """Return one labelled preference group."""
    children: list[object] = [
        html.Div(
            [html.H2(title), html.P(description)],
            className="q-setting-heading",
        ),
        html.Div(control, className="q-setting-control"),
    ]
    if note:
        children.append(html.P(note, className="q-setting-note"))
    return html.Section(children, className="q-panel q-setting-group")


def option_cards(
    component_id: str,
    options: Sequence[Option],
    *,
    value: str,
) -> dcc.RadioItems:
    """Return a radio selector rendered as descriptive option cards."""
    return dcc.RadioItems(
        id=component_id,
        options=[
            {
                "label": html.Div(
                    [html.Strong(label), html.Span(description)],
                    className="q-setting-option-copy",
                ),
                "value": option_value,
            }
            for label, option_value, description in options
        ],
        value=value,
        className="q-setting-options",
        inputClassName="q-setting-option-input",
        labelClassName="q-setting-option",
    )


def settings_preview() -> html.Section:
    """Return a compact preview using the active interface preferences."""
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Preview", className="q-eyebrow"),
                            html.H2("Scientific interface preview"),
                            html.P(
                                "Typography, surfaces, controls, and data density update "
                                "without changing numerical values or result files."
                            ),
                        ]
                    ),
                    html.Span("float64", className="q-status-pill is-info"),
                ],
                className="q-settings-preview-header",
            ),
            html.Div(
                [
                    html.Div(
                        [html.Small("Pressure"), html.Strong("5.000 GPa")],
                        className="q-settings-preview-metric",
                    ),
                    html.Div(
                        [html.Small("Temperature"), html.Strong("800.0 K")],
                        className="q-settings-preview-metric",
                    ),
                    html.Div(
                        [html.Small("Bulk modulus"), html.Strong("92.47 GPa")],
                        className="q-settings-preview-metric",
                    ),
                ],
                className="q-settings-preview-grid",
            ),
            html.Div(
                [
                    html.Button("Primary action", className="q-button q-button--primary"),
                    html.Button("Secondary action", className="q-button"),
                ],
                className="q-settings-preview-actions",
            ),
        ],
        className="q-panel q-settings-preview",
    )


def developer_tools_link() -> html.Div:
    """Return a link to the reusable Scientific UI Kit."""
    return html.Div(
        [
            html.Div(
                [
                    html.Strong("Scientific UI Kit"),
                    html.Span(
                        "Inspect reusable inputs, matrices, tables, logs, and feedback components."
                    ),
                ]
            ),
            dcc.Link(
                "Open UI Kit",
                href=dash.get_relative_path("/ui-kit"),
                className="q-button",
            ),
        ],
        className="q-panel q-settings-developer-link",
    )
