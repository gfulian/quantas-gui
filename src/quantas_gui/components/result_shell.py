"""Application shell and file-opening components for the Results Explorer."""

from __future__ import annotations

from typing import Any

from dash import dcc, html

from quantas_gui.components.controls import action_button
from quantas_gui.components.result_components import format_bytes
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.models.results import ResultReference, ResultSummary


def explorer_layout() -> html.Div:
    """Create the complete Results Explorer shell and lazy content region."""
    return html.Div(
        [
            dcc.Store(id=ResultIds.SESSION, storage_type="session"),
            dcc.Store(id=ResultIds.PLOT_INVENTORY, storage_type="memory"),
            dcc.Download(id=ResultIds.DOWNLOAD_ORIGINAL_PAYLOAD),
            dcc.Download(id=ResultIds.DOWNLOAD_REPORT_PAYLOAD),
            dcc.Download(id=ResultIds.TABLE_DOWNLOAD_PAYLOAD),
            html.Div(
                [
                    html.Section(
                        [
                            html.Div("Native HDF5 inspection", className="q-eyebrow"),
                            html.H1("Results Explorer"),
                            html.P(
                                "Open a native Quantas result, inspect its scientific provenance, "
                                "render neutral tables, and explore Plotly figures without moving "
                                "large numerical payloads into the browser session."
                            ),
                        ],
                        className="q-page-intro q-result-page-intro",
                    ),
                    dcc.Upload(
                        id=ResultIds.UPLOAD_COMPACT,
                        children=html.Div([html.Span("＋"), html.Span("Open result")]),
                        className="q-button q-result-compact-upload",
                        multiple=False,
                    ),
                ],
                className="q-result-intro-row",
            ),
            html.Div(id=ResultIds.ALERT, className="q-alert-region", role="status"),
            upload_panel(),
            html.Div(
                [
                    html.Div(id=ResultIds.HEADER),
                    _result_tabs(),
                    dcc.Loading(
                        html.Div(
                            id=ResultIds.TAB_CONTENT,
                            className="q-result-tab-content",
                        ),
                        type="circle",
                        color="#69bce8",
                        className="q-result-loading",
                    ),
                ],
                id=ResultIds.WORKSPACE,
                className="q-result-workspace is-hidden",
            ),
        ],
        className="q-content q-results-explorer",
    )


def upload_panel(*, compact: bool = False) -> html.Section:
    """Create the primary or compact HDF5 upload surface."""
    upload_id = ResultIds.UPLOAD_COMPACT if compact else ResultIds.UPLOAD
    children = html.Div(
        [
            html.Span("H5", className="q-upload-icon"),
            html.Div(
                [
                    html.Strong("Drop a native Quantas result here"),
                    html.Small("or choose an .h5, .hdf5, or .hdf file"),
                ]
            ),
        ],
        className="q-upload-copy",
    )
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Open a Quantas result"),
                            html.P(
                                "The file is copied into an isolated GUI workspace, validated "
                                "through quantas.api.registry, and reopened lazily for each view."
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Span("Local-first", className="q-status-pill is-info"),
                            html.Span("Server-ready", className="q-status-pill is-success"),
                        ],
                        className="q-upload-badges",
                    ),
                ],
                className="q-result-open-heading",
            ),
            dcc.Upload(
                id=upload_id,
                children=children,
                className=("q-upload-zone q-upload-zone--compact" if compact else "q-upload-zone"),
                multiple=False,
            ),
            html.Div(
                [
                    feature_note("Metadata-driven", "No filename-based module guessing."),
                    feature_note(
                        "Lazy rendering",
                        "Tables and figures are built only when opened.",
                    ),
                    feature_note(
                        "Opaque references",
                        "The browser never receives server file paths.",
                    ),
                ],
                className="q-result-open-notes",
            ),
        ],
        id=None if compact else ResultIds.UPLOAD_PANEL,
        className=(
            "q-panel q-result-open-panel q-result-open-panel--compact"
            if compact
            else "q-panel q-result-open-panel"
        ),
    )


def feature_note(title: str, text: str) -> html.Div:
    """Create one compact architectural note below the upload surface."""
    return html.Div(
        [
            html.Span("✓", className="q-feature-check"),
            html.Div([html.Strong(title), html.Small(text)]),
        ],
        className="q-feature-note",
    )


def alert(message: str, *, level: str = "info") -> html.Div:
    """Create a dismiss-free inline alert for upload and renderer errors."""
    icon = {"success": "✓", "warning": "!", "error": "×"}.get(level, "i")
    return html.Div(
        [html.Span(icon, className="q-alert-icon"), html.Span(message)],
        className=f"q-alert is-{level}",
    )


def result_header(reference: ResultReference, summary: ResultSummary) -> html.Section:
    """Create the persistent identity and action header for an open result."""
    subtitle_parts = [summary.method or "Unknown method"]
    if summary.schema_version:
        subtitle_parts.append(f"schema {summary.schema_version}")
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                summary.module.upper(),
                                className="q-result-module-badge",
                            ),
                            html.Span(
                                "Archive" if summary.archive else "Result envelope",
                                className="q-status-pill is-info",
                            ),
                        ],
                        className="q-result-badges",
                    ),
                    html.H2(summary.module_title),
                    html.P(" · ".join(subtitle_parts)),
                    html.Div(
                        [
                            html.Span(
                                reference.filename,
                                className="q-result-filename",
                            ),
                            html.Span(format_bytes(reference.size_bytes)),
                        ],
                        className="q-result-fileline",
                    ),
                ],
                className="q-result-identity",
            ),
            html.Div(
                [
                    action_button(
                        "Plain report",
                        component_id=ResultIds.DOWNLOAD_REPORT,
                        icon="↓",
                    ),
                    action_button(
                        "Original HDF5",
                        component_id=ResultIds.DOWNLOAD_ORIGINAL,
                        icon="↓",
                    ),
                    action_button(
                        "Close",
                        component_id=ResultIds.CLOSE,
                        icon="×",
                        danger=True,
                    ),
                ],
                className="q-result-actions",
            ),
        ],
        className="q-panel q-result-header",
    )


def _result_tabs() -> dcc.Tabs:
    tabs: list[Any] = []
    for label, value in (
        ("Overview", "overview"),
        ("Tables", "tables"),
        ("Plots", "plots"),
        ("Messages", "messages"),
        ("Data", "data"),
    ):
        tabs.append(
            dcc.Tab(
                label=label,
                value=value,
                className="q-result-tab",
                selected_className="q-result-tab q-result-tab--selected",
            )
        )
    return dcc.Tabs(
        id=ResultIds.TABS,
        value="overview",
        children=tabs,
        className="q-result-tabs",
        parent_className="q-result-tabs-shell",
    )
