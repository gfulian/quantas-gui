"""Shared presentational primitives for result inspection views."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any

from dash import html

from quantas_gui.models.results import EventView


def panel(
    title: str,
    children: Sequence[Any],
    *,
    kicker: str | None = None,
    extra_class: str = "",
) -> html.Section:
    """Create a reusable titled result panel."""
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(kicker, className="q-panel-kicker") if kicker else None,
                            html.H3(title),
                        ]
                    )
                ],
                className="q-panel-header q-result-panel-header",
            ),
            html.Div(list(children), className="q-result-panel-body"),
        ],
        className=f"q-panel q-result-panel {extra_class}".strip(),
    )


def key_value_row(label: str, value: Any) -> html.Div:
    """Create one provenance key-value row."""
    return html.Div(
        [html.Span(label), html.Strong(str(value))],
        className="q-key-value-row",
    )


def event_row(event: EventView, *, compact: bool) -> html.Div:
    """Create one level-aware workflow event row."""
    level = event.level.lower().split(".")[-1]
    body: list[Any] = [
        html.Div(
            [
                html.Span(level.upper(), className=f"q-event-level is-{level}"),
                html.Time(format_datetime(event.timestamp)) if event.timestamp else None,
            ],
            className="q-event-meta",
        ),
        html.P(event.message),
    ]
    if not compact and event.data:
        body.append(
            html.Pre(
                json.dumps(event.data, indent=2, ensure_ascii=False),
                className="q-event-data",
            )
        )
    return html.Div(
        [html.Span(className=f"q-event-dot is-{level}"), html.Div(body)],
        className="q-event-row is-compact" if compact else "q-event-row",
    )


def json_details(
    title: str,
    values: Any,
    *,
    open_by_default: bool = False,
) -> html.Details:
    """Create a collapsible bounded JSON block."""
    return html.Details(
        [
            html.Summary([html.Span(title), html.Span("JSON", className="q-json-badge")]),
            html.Pre(json.dumps(values, indent=2, ensure_ascii=False, default=str)),
        ],
        open=open_by_default,
        className="q-json-panel q-panel",
    )


def empty_result_section(title: str, message: str) -> html.Section:
    """Create a reusable empty renderer state."""
    return html.Section(
        [html.Span("◇", className="q-empty-icon"), html.H3(title), html.P(message)],
        className="q-empty-renderer q-panel",
    )


def format_bytes(value: int) -> str:
    """Format a byte count for compact display."""
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(amount) < 1024.0 or unit == "TiB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.2f} {unit}"
        amount /= 1024.0
    return f"{amount:.2f} TiB"


def format_datetime(value: str | None) -> str:
    """Format an ISO date without failing on legacy or absent values."""
    if not value:
        return "not persisted"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def event_timeline_rows(
    events: Iterable[EventView],
    warnings: Sequence[str] = (),
) -> list[Any]:
    """Return warning and event rows in persistent workflow order."""
    rows: list[Any] = [
        event_row(EventView(level="warning", message=message), compact=False)
        for message in warnings
    ]
    rows.extend(event_row(event, compact=False) for event in events)
    return rows
