"""Reusable status, progress, log, and validation components."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from dash import html

MessageLevel = Literal["info", "progress", "result", "warning", "error"]


def status_badge(label: str, *, level: MessageLevel = "info") -> html.Span:
    """Return a compact semantic status badge."""
    return html.Span(label, className=f"q-status-badge q-status-badge--{level}")


def message_banner(
    *,
    title: str,
    message: str,
    level: MessageLevel = "info",
    details: str | None = None,
) -> html.Div:
    """Create an accessible informational, warning, or error banner."""
    symbols = {
        "info": "i",
        "progress": "↻",
        "result": "✓",
        "warning": "!",
        "error": "×",
    }
    return html.Div(
        [
            html.Div(
                symbols[level],
                className="q-message-icon",
                **{"aria-hidden": "true"},
            ),
            html.Div(
                [
                    html.Strong(title),
                    html.P(message),
                    html.Details(
                        [html.Summary("Technical details"), html.Pre(details)],
                        className="q-message-details",
                    )
                    if details
                    else None,
                ],
                className="q-message-content",
            ),
        ],
        className=f"q-message q-message--{level}",
        role="alert" if level in {"warning", "error"} else "status",
    )


def progress_panel(
    *,
    title: str,
    progress: float,
    message: str | None = None,
    current: int | None = None,
    total: int | None = None,
    indeterminate: bool = False,
) -> html.Div:
    """Render calculation progress without storing it in scientific results."""
    bounded = min(max(float(progress), 0.0), 1.0)
    percent = int(round(100.0 * bounded))
    counter = f"{current} / {total}" if current is not None and total is not None else None
    bar = html.Div(
        html.Div(
            className="q-progress-fill q-progress-fill--indeterminate"
            if indeterminate
            else "q-progress-fill",
            style={} if indeterminate else {"width": f"{percent}%"},
        ),
        className="q-progress-track",
        role="progressbar",
        **{
            "aria-valuemin": "0",
            "aria-valuemax": "100",
            "aria-valuenow": None if indeterminate else str(percent),
        },
    )
    return html.Div(
        [
            html.Div(
                [html.Strong(title), html.Span(counter or f"{percent}%")],
                className="q-progress-heading",
            ),
            bar,
            html.P(message, className="q-progress-message") if message else None,
        ],
        className="q-progress-panel q-panel",
    )


def log_viewer(
    lines: Sequence[str] | str,
    *,
    title: str = "Calculation log",
    level: MessageLevel = "info",
    empty_message: str = "No messages yet.",
) -> html.Div:
    """Create a scrollable monospaced log viewer."""
    text = lines if isinstance(lines, str) else "\n".join(lines)
    return html.Div(
        [
            html.Div(
                [html.Strong(title), status_badge(level.upper(), level=level)],
                className="q-log-heading",
            ),
            html.Pre(text or empty_message, className="q-log-output", tabIndex=0),
        ],
        className="q-log-viewer q-panel",
    )


def validation_summary(
    issues: Sequence[Any],
    *,
    title: str = "Check the highlighted fields",
) -> html.Div | None:
    """Render a form-level summary from validation issue-like objects."""
    if not issues:
        return None
    items = []
    for issue in issues:
        field = getattr(issue, "field", None)
        message = str(getattr(issue, "message", issue))
        items.append(html.Li([html.Code(field) if field else None, html.Span(message)]))
    return html.Div(
        [html.Strong(title), html.Ul(items)],
        className="q-validation-summary",
        role="alert",
    )


def structured_result_panel(
    *,
    title: str,
    data: Mapping[str, Any],
    level: MessageLevel = "result",
) -> html.Div:
    """Render a concise structured result emitted by a workflow."""
    rows = [
        html.Div(
            [html.Span(str(key)), html.Strong(str(value))],
            className="q-structured-result-row",
        )
        for key, value in data.items()
    ]
    return html.Div(
        [
            html.Div(
                [html.Strong(title), status_badge(level.upper(), level=level)],
                className="q-structured-result-heading",
            ),
            html.Div(rows, className="q-structured-result-body"),
        ],
        className="q-structured-result q-panel",
    )


__all__ = [
    "MessageLevel",
    "log_viewer",
    "message_banner",
    "progress_panel",
    "status_badge",
    "structured_result_panel",
    "validation_summary",
]
