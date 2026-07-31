"""Dash presentation helpers for Elasticity job and completion states."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from dash import dcc, html

from quantas_gui.components.controls import action_button
from quantas_gui.components.feedback import (
    MessageLevel,
    log_viewer,
    message_banner,
    progress_panel,
    structured_result_panel,
)
from quantas_gui.renderers.tables import table_component
from quantas_gui.services.backends import JobState, JobStatus
from quantas_gui.workflows.elasticity.ids import ElasticityIds


def queued_view() -> html.Div:
    """Return the immediate non-blocking acknowledgement after submit."""
    return html.Div(
        [
            message_banner(
                title="Calculation queued",
                message="The request was persisted and assigned to a separate worker process.",
                level="progress",
            ),
            progress_panel(
                title="Queued",
                progress=0.0,
                message="Waiting for the local Elasticity worker to start.",
                indeterminate=True,
            ),
            action_button(
                "Cancel calculation",
                component_id=ElasticityIds.CANCEL,
                danger=True,
            ),
        ],
        className="q-workflow-runtime-stack",
    )


def active_job_view(status: JobStatus, events: Sequence[Mapping[str, Any]]) -> html.Div:
    """Render queued, running, or cancelling state."""
    current, total = latest_counter(events)
    if status.state is JobState.CANCELLING:
        banner = message_banner(
            title="Cancelling calculation",
            message="The worker will stop at the next safe Quantas event or checkpoint.",
            level="warning",
        )
        cancel = action_button(
            "Cancellation requested",
            component_id=ElasticityIds.CANCEL,
            danger=True,
            disabled=True,
        )
    else:
        banner = message_banner(
            title="Elasticity calculation in progress",
            message="The browser can be refreshed or closed without terminating the local job.",
            level="progress",
        )
        cancel = action_button(
            "Cancel calculation",
            component_id=ElasticityIds.CANCEL,
            danger=True,
        )
    progress = status.progress
    return html.Div(
        [
            banner,
            progress_panel(
                title=_state_label(status.state),
                progress=0.0 if progress is None else progress,
                message=status.message or "Quantas is processing the request.",
                current=current,
                total=total,
                indeterminate=progress is None,
            ),
            cancel,
        ],
        className="q-workflow-runtime-stack",
    )


def failed_view(status: JobStatus, *, cancelled: bool = False) -> html.Div:
    """Render one failed or safely cancelled terminal state."""
    if cancelled:
        banner = message_banner(
            title="Calculation cancelled",
            message="The job stopped at a safe checkpoint. No result was published.",
            level="warning",
        )
    else:
        banner = message_banner(
            title="Calculation failed",
            message=(
                "The Elasticity calculation did not complete correctly. "
                "No valid HDF5 result was published."
            ),
            level="error",
            details=status.error,
        )
    return html.Div(
        [
            banner,
            html.Div(
                [
                    action_button("Back to input", component_id=ElasticityIds.BACK),
                    action_button(
                        "Download diagnostic log",
                        component_id=ElasticityIds.DOWNLOAD_DIAGNOSTIC,
                    ),
                ],
                className="q-workflow-actions",
            ),
        ],
        className="q-workflow-runtime-stack",
    )


def success_view(
    *,
    jobname: str,
    warning_count: int,
    events: Sequence[Mapping[str, Any]],
    tables: Sequence[Any],
) -> html.Div:
    """Render the compact workflow completion summary and essential tables."""
    crystal_system = latest_event_value(events, "crystal_system") or "Unknown"
    stable_value = latest_event_value(events, "stable")
    if stable_value is None:
        stable_value = latest_event_value(events, "is_stable")
    if isinstance(stable_value, bool):
        stability = "Mechanically stable" if stable_value else "Mechanically unstable"
    else:
        stability = "See stability table"

    if warning_count:
        banner = message_banner(
            title="Calculation completed with warnings",
            message=(
                "The native result is valid, but one or more scientific warnings require attention."
            ),
            level="warning",
        )
    else:
        banner = message_banner(
            title="Calculation completed successfully",
            message="The native Quantas Elasticity result was published atomically.",
            level="result",
        )

    essential_titles = {
        "Voigt-Reuss-Hill average properties",
        "Mechanical stability",
        "Directional elastic extrema",
    }
    essential = [table for table in tables if str(table.title) in essential_titles]
    remaining = [table for table in tables if str(table.title) not in essential_titles]
    essential_components = [
        table_component(table, component_id=f"q-elasticity-summary-table-{index}", page_size=10)
        for index, table in enumerate(essential)
    ]
    full_components = [
        table_component(table, component_id=f"q-elasticity-report-table-{index}", page_size=10)
        for index, table in enumerate(remaining)
    ]

    return html.Div(
        [
            banner,
            structured_result_panel(
                title="Elasticity result",
                data={
                    "Job": jobname,
                    "Crystal system": crystal_system,
                    "Mechanical stability": stability,
                    "Warnings": warning_count,
                },
            ),
            html.Div(essential_components, className="q-workflow-summary-tables"),
            html.Details(
                [
                    html.Summary("Full report tables"),
                    html.Div(full_components, className="q-workflow-summary-tables"),
                ],
                className="q-panel q-workflow-report-details",
            )
            if full_components
            else None,
            html.Div(
                [
                    action_button(
                        "Download HDF5",
                        component_id=ElasticityIds.DOWNLOAD_HDF5,
                        primary=True,
                    ),
                    action_button(
                        "Download report",
                        component_id=ElasticityIds.DOWNLOAD_REPORT,
                    ),
                    action_button(
                        "Open in Result Explorer",
                        component_id=ElasticityIds.OPEN_RESULTS,
                        primary=True,
                    ),
                    action_button("Back to input", component_id=ElasticityIds.BACK),
                ],
                className="q-workflow-actions",
            ),
        ],
        className="q-workflow-summary-stack",
    )


def activity_tabs() -> dcc.Tabs:
    """Return the static activity filter tabs."""
    return dcc.Tabs(
        id=ElasticityIds.ACTIVITY_TABS,
        value="all",
        children=[
            dcc.Tab(label="All", value="all"),
            dcc.Tab(label="Info", value="info"),
            dcc.Tab(label="Warnings", value="warning"),
            dcc.Tab(label="Errors", value="error"),
        ],
        className="q-workflow-activity-tabs",
    )


def activity_view(
    events: Sequence[Mapping[str, Any]],
    selected: str,
) -> html.Div:
    """Render a bounded read-only event log for one selected severity."""
    filtered = []
    for event in events:
        event_level = str(event.get("level", "info")).lower()
        if selected == "info" and event_level in {"warning", "error"}:
            continue
        if selected in {"warning", "error"} and event_level != selected:
            continue
        filtered.append(_event_line(event))
    viewer_level: MessageLevel = (
        "error" if selected == "error" else "warning" if selected == "warning" else "info"
    )
    return log_viewer(
        filtered,
        title="Calculation activity",
        level=viewer_level,
        empty_message="No messages in this category.",
    )


def diagnostic_text(events: Sequence[Mapping[str, Any]], status: Mapping[str, Any] | None) -> str:
    """Return a deterministic lightweight diagnostic log."""
    lines = ["Quantas GUI Elasticity diagnostic log"]
    if status:
        lines.extend(
            [
                f"state: {status.get('state', 'unknown')}",
                f"message: {status.get('message', '')}",
                f"error: {status.get('error', '')}",
                "",
            ]
        )
    lines.extend(_event_line(event) for event in events)
    return "\n".join(lines).rstrip() + "\n"


def latest_counter(events: Sequence[Mapping[str, Any]]) -> tuple[int | None, int | None]:
    """Return the newest useful current/total progress pair."""
    for event in reversed(events):
        data = event.get("data", {})
        if not isinstance(data, Mapping):
            continue
        current = data.get("current")
        total = data.get("total")
        if isinstance(current, int) and isinstance(total, int):
            return current, total
    return None, None


def latest_event_value(events: Sequence[Mapping[str, Any]], key: str) -> object | None:
    """Return the newest scalar event datum with the requested key."""
    for event in reversed(events):
        data = event.get("data", {})
        if isinstance(data, Mapping) and key in data:
            return data[key]
    return None


def _event_line(event: Mapping[str, Any]) -> str:
    created_at = event.get("created_at")
    if isinstance(created_at, (int, float, str)):
        try:
            timestamp = datetime.fromtimestamp(float(created_at)).strftime("%H:%M:%S")
        except (ValueError, OSError):
            timestamp = "--:--:--"
    else:
        timestamp = "--:--:--"
    level = str(event.get("level", "info")).upper()
    symbol = {"INFO": "ⓘ", "PROGRESS": "↻", "RESULT": "✓", "WARNING": "⚠", "ERROR": "×"}.get(
        level,
        "·",
    )
    return f"{timestamp}  {symbol}  {level:<8} {event.get('message', '')}"


def _state_label(state: JobState) -> str:
    return {
        JobState.QUEUED: "Queued",
        JobState.RUNNING: "Running",
        JobState.CANCELLING: "Cancelling",
    }.get(state, state.value.capitalize())


__all__ = [
    "active_job_view",
    "activity_tabs",
    "activity_view",
    "diagnostic_text",
    "failed_view",
    "latest_counter",
    "queued_view",
    "success_view",
]
