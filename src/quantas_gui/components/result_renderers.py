"""Table, Plotly, message, and bounded-data views for the Results Explorer."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from dash import dcc, html

from quantas_gui.components.controls import action_button
from quantas_gui.components.renderer_controls import (
    camera_selector,
    colorbar_toggle,
    colormap_selector,
    contour_toggles,
    family_note,
    family_selector,
    hover_selector,
    message_level_selector,
    message_search_control,
    page_size_selector,
    plot_selector,
    plot_visibility_toggles,
    renderer_toolbar,
    spherical_projection_selector,
    surface_opacity_control,
    table_selector,
)
from quantas_gui.components.result_components import (
    empty_result_section,
    event_timeline_rows,
    json_details,
    panel,
)
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor
from quantas_gui.models.results import EventView, ResultOverview
from quantas_gui.renderers.plotly import PlotDescriptor
from quantas_gui.renderers.tables import table_component


def tables_view(families: Sequence[TableFamilyDescriptor]) -> html.Div:
    """Create the report-family shell without building report tables."""
    if not families:
        return empty_result_section(
            "No report families",
            "This result exposes no report tables.",
        )
    selected = next((item for item in families if item.default), families[0])
    return html.Div(
        [
            renderer_toolbar(
                [
                    family_selector(
                        component_id=ResultIds.TABLE_FAMILY,
                        label="Report family",
                        families=families,
                    ),
                    page_size_selector(component_id=ResultIds.TABLE_PAGE_SIZE),
                ],
                actions=[
                    action_button(
                        "Download CSV",
                        component_id=ResultIds.TABLE_DOWNLOAD,
                        icon="↓",
                    )
                ],
            ),
            html.Div(
                family_note(selected),
                id=ResultIds.TABLE_FAMILY_INFO,
            ),
            dcc.Loading(
                html.Div(id=ResultIds.TABLE_VIEW),
                type="circle",
                color="#69bce8",
                className="q-result-loading",
            ),
        ],
        className="q-result-section-stack",
    )


def rendered_tables_view(
    tables: Sequence[Any],
    *,
    page_size: int = 50,
    groups: Sequence[str] | None = None,
) -> html.Div:
    """Create a table selector and first prepared AG Grid table."""
    if not tables:
        return empty_result_section(
            "No report tables",
            "The selected report family is empty.",
        )
    return html.Div(
        [
            html.Div(
                renderer_toolbar(
                    [
                        table_selector(
                            component_id=ResultIds.TABLE_SELECTOR,
                            tables=tables,
                            groups=groups,
                        )
                    ]
                ),
                id=ResultIds.TABLE_SELECTOR_HOST,
            ),
            html.Div(
                table_component(
                    tables[0],
                    component_id="q-result-table",
                    page_size=page_size,
                ),
                id=ResultIds.TABLE_GRID,
            ),
        ],
        className="q-result-section-stack",
    )


def plots_view(families: Sequence[PlotFamilyDescriptor]) -> html.Div:
    """Create a lazy module-aware Plotly family shell."""
    if not families:
        return empty_result_section(
            "No plot families",
            (
                "This result exposes no generic plot family. "
                "EOS fit visualization is session-oriented."
            ),
        )
    selected = next((item for item in families if item.default), families[0])
    return html.Div(
        [
            renderer_toolbar(
                [
                    family_selector(
                        component_id=ResultIds.PLOT_FAMILY,
                        label="Scientific view",
                        families=families,
                    )
                ]
            ),
            html.Div(
                family_note(selected),
                id=ResultIds.PLOT_FAMILY_INFO,
            ),
            dcc.Loading(
                html.Div(
                    id=ResultIds.PLOT_SELECTOR_HOST,
                    className="q-plot-selector-host",
                ),
                type="circle",
                color="#69bce8",
                className="q-result-loading",
            ),
            html.Div(
                id=ResultIds.PLOT_DESCRIPTION,
                className="q-plot-description",
            ),
            plot_control_drawer(),
            html.Div(
                [
                    dcc.Loading(
                        dcc.Graph(
                            id=ResultIds.PLOT_VIEW,
                            config={
                                "displaylogo": False,
                                "responsive": True,
                                "scrollZoom": True,
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "quantas-figure",
                                    "scale": 2,
                                },
                            },
                            responsive=True,
                            className="q-plotly-graph",
                        ),
                        type="circle",
                        color="#69bce8",
                        className="q-result-loading",
                    )
                ],
                className="q-panel q-plot-panel",
            ),
        ],
        className="q-result-section-stack",
    )


def loaded_plot_selector(
    plots: Sequence[PlotDescriptor], *, warnings: Sequence[str] = ()
) -> html.Div:
    """Create the selector for one already cached scientific family."""
    if not plots:
        details = " ".join(warnings) if warnings else "No figures were generated."
        return empty_result_section("No plot specifications", details)
    return html.Div(
        [
            renderer_toolbar(
                [
                    plot_selector(
                        component_id=ResultIds.PLOT_SELECTOR,
                        plots=plots,
                    )
                ]
            ),
            *[_warning_alert(message) for message in warnings],
        ]
    )


def plot_control_drawer() -> html.Details:
    """Create responsive controls that are revealed according to plot kind."""
    return html.Details(
        [
            html.Summary(
                [
                    html.Span("Figure controls"),
                    html.Small("Display only · scientific data unchanged"),
                ]
            ),
            html.Div(
                [
                    html.Div(
                        colormap_selector(component_id=ResultIds.PLOT_COLORMAP),
                        id=ResultIds.PLOT_COLORMAP_WRAP,
                        className="q-plot-control is-hidden",
                    ),
                    html.Div(
                        hover_selector(component_id=ResultIds.PLOT_HOVER),
                        id=ResultIds.PLOT_HOVER_WRAP,
                        className="q-plot-control",
                    ),
                    html.Div(
                        spherical_projection_selector(component_id=ResultIds.PLOT_PROJECTION),
                        id=ResultIds.PLOT_PROJECTION_WRAP,
                        className="q-plot-control is-hidden",
                    ),
                    html.Div(
                        contour_toggles(component_id=ResultIds.PLOT_CONTOUR_OPTIONS),
                        id=ResultIds.PLOT_CONTOUR_WRAP,
                        className="q-plot-control is-hidden",
                    ),
                    html.Div(
                        [
                            surface_opacity_control(component_id=ResultIds.PLOT_SURFACE_OPACITY),
                            camera_selector(component_id=ResultIds.PLOT_CAMERA),
                            colorbar_toggle(component_id=ResultIds.PLOT_COLORBAR),
                        ],
                        id=ResultIds.PLOT_SURFACE_WRAP,
                        className=("q-plot-control q-plot-surface-controls is-hidden"),
                    ),
                    html.Div(
                        plot_visibility_toggles(component_id=ResultIds.PLOT_OPTIONS),
                        className="q-plot-control q-plot-control--toggles",
                    ),
                ],
                className="q-plot-controls-grid",
            ),
        ],
        id=ResultIds.PLOT_CONTROL_DRAWER,
        className="q-plot-control-drawer q-panel",
    )


def messages_view(overview: ResultOverview) -> html.Div:
    """Create stored-event controls and the initial message timeline."""
    levels = sorted({event.level for event in overview.events})
    controls = renderer_toolbar(
        [
            message_level_selector(
                component_id=ResultIds.MESSAGE_LEVELS,
                levels=levels,
            ),
            message_search_control(component_id=ResultIds.MESSAGE_SEARCH),
        ]
    )
    return html.Div(
        [
            controls,
            html.Div(
                message_timeline(overview.events, overview.warnings),
                id=ResultIds.MESSAGE_VIEW,
            ),
        ],
        className="q-result-section-stack",
    )


def message_timeline(events: Iterable[EventView], warnings: Sequence[str] = ()) -> html.Section:
    """Create the persisted warning and event timeline."""
    rows = event_timeline_rows(events, warnings)
    if not rows:
        return empty_result_section(
            "No stored messages",
            "This result has no warnings or events.",
        )
    return panel(
        "Workflow history",
        rows,
        kicker="Warnings, errors, information, and results",
    )


def data_view(overview: ResultOverview) -> html.Div:
    """Create the bounded technical-data view."""
    payload = [item.as_dict() for item in overview.inventory]
    return html.Div(
        [
            json_details(
                "Metadata",
                overview.metadata,
                open_by_default=True,
            ),
            json_details("Normalized input", overview.input_data),
            json_details("Options", overview.options),
            json_details("Payload inventory", payload),
            html.Div(
                [
                    html.Strong("Large arrays remain server-side"),
                    html.P(
                        "Only type, shape, dtype, and bounded previews are "
                        "shown here. The native HDF5 values are never rounded "
                        "or copied into browser state."
                    ),
                ],
                className="q-data-policy q-panel",
            ),
        ],
        className="q-data-grid",
    )


def _warning_alert(message: str) -> html.Div:
    return html.Div(
        [
            html.Span("!", className="q-alert-icon"),
            html.Span(message),
        ],
        className="q-alert is-warning",
    )
