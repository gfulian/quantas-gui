"""Overview and provenance views for native Quantas results."""

from __future__ import annotations

from typing import Any, Sequence

from dash import html

from quantas_gui.components.result_components import (
    event_row,
    format_bytes,
    format_datetime,
    key_value_row,
    panel,
)
from quantas_gui.models.results import EventView, ResultOverview, ResultReference


def overview_view(reference: ResultReference, overview: ResultOverview) -> html.Div:
    """Create the default overview with provenance, warnings, and inventory."""
    summary = overview.summary
    metrics = [
        metric_card("Module", summary.module.upper(), summary.module_title),
        metric_card("Method", summary.method or "Unknown", "Persisted workflow method"),
        metric_card(
            "Warnings",
            str(summary.warning_count),
            "Scientific and workflow warnings",
        ),
        metric_card("Events", str(summary.event_count), "Persisted meaningful messages"),
    ]
    return html.Div(
        [
            html.Div(metrics, className="q-result-metrics"),
            html.Div(
                [metadata_panel(reference, overview), warning_panel(overview.warnings)],
                className="q-result-overview-grid",
            ),
            inventory_panel(overview),
            recent_messages_panel(overview.events),
        ],
        className="q-result-section-stack",
    )


def metric_card(label: str, value: str, note: str) -> html.Article:
    """Create one compact result metric card."""
    return html.Article(
        [html.Span(label), html.Strong(value), html.Small(note)],
        className="q-result-metric q-panel",
    )


def metadata_panel(reference: ResultReference, overview: ResultOverview) -> html.Section:
    """Create a key-value provenance panel."""
    rows = [
        ("Program", overview.summary.program or "unknown"),
        ("Quantas version", overview.summary.quantas_version or "not persisted"),
        ("Schema", overview.summary.schema_version or "unknown"),
        ("Created", format_datetime(overview.summary.created_at)),
        ("Creator", overview.summary.created_by or "not persisted"),
        ("File", reference.filename),
        ("Size", format_bytes(reference.size_bytes)),
    ]
    return panel(
        "Provenance",
        [key_value_row(label, value) for label, value in rows],
        kicker="Native metadata",
    )


def warning_panel(warnings: Sequence[str]) -> html.Section:
    """Create a warning summary that remains visible outside Messages."""
    if not warnings:
        content: list[Any] = [
            html.Div(
                [
                    html.Span("✓"),
                    html.Div(
                        [
                            html.Strong("No stored warnings"),
                            html.P(
                                "The result envelope contains no warning messages."
                            ),
                        ]
                    ),
                ],
                className="q-clean-state",
            )
        ]
    else:
        content = [
            html.Div([html.Span("!"), html.P(message)], className="q-warning-row")
            for message in warnings[:6]
        ]
        if len(warnings) > 6:
            content.append(
                html.Small(f"{len(warnings) - 6} additional warnings in Messages")
            )
    return panel("Warnings", content, kicker="Scientific attention")


def inventory_panel(overview: ResultOverview) -> html.Section:
    """Create a structural inventory without expanding numerical arrays."""
    rows: list[Any] = []
    for item in overview.inventory:
        shape = "—" if item.shape is None else " × ".join(str(value) for value in item.shape)
        rows.append(
            html.Div(
                [
                    html.Code(item.key),
                    html.Span(item.value_type),
                    html.Span(shape),
                    html.Span(item.dtype or item.summary or "—"),
                ],
                className="q-inventory-row",
            )
        )
    if not rows:
        rows = [
            html.P("No scientific payload inventory is available.", className="q-muted")
        ]
    return panel(
        "Result payload",
        rows,
        kicker="Server-side inventory",
        extra_class="q-inventory-panel",
    )


def recent_messages_panel(events: Sequence[EventView]) -> html.Section:
    """Create a compact preview of the most recent persisted messages."""
    if not events:
        content: list[Any] = [html.P("No persisted workflow events.", className="q-muted")]
    else:
        content = [event_row(event, compact=True) for event in events[-5:][::-1]]
    return panel("Recent messages", content, kicker="Persistent workflow history")
