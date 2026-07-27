"""Small reusable form and toolbar controls."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dash import dcc, html


def labelled_dropdown(
    *,
    component_id: str,
    label: str,
    options: Sequence[dict[str, Any]],
    value: Any = None,
    clearable: bool = False,
    searchable: bool = True,
    multi: bool = False,
    class_name: str = "",
) -> html.Label:
    """Create a compact labelled Dash dropdown used by renderer toolbars."""
    return html.Label(
        [
            html.Span(label, className="q-control-label"),
            dcc.Dropdown(
                id=component_id,
                options=list(options),
                value=value,
                clearable=clearable,
                searchable=searchable,
                multi=multi,
                className="q-dropdown",
            ),
        ],
        className=f"q-control {class_name}".strip(),
    )


def action_button(
    label: str,
    *,
    component_id: str | dict[str, Any],
    icon: str | None = None,
    primary: bool = False,
    danger: bool = False,
    disabled: bool = False,
) -> html.Button:
    """Create a reusable action button with consistent visual states."""
    modifiers = ["q-button"]
    if primary:
        modifiers.append("q-button--primary")
    if danger:
        modifiers.append("q-button--danger")
    return html.Button(
        [html.Span(icon, className="q-button-icon") if icon else None, html.Span(label)],
        id=component_id,
        className=" ".join(modifiers),
        disabled=disabled,
        type="button",
    )
