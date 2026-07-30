"""Table, Plotly, message, and bounded-data views for the Results Explorer."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from dash import dcc, html

from quantas_gui.components.controls import action_button, labelled_dropdown
from quantas_gui.components.renderer_controls import (
    axis_label_mode_selector,
    camera_selector,
    colorbar_toggle,
    colormap_selector,
    contour_level_control,
    contour_toggles,
    family_note,
    family_selector,
    hover_selector,
    line_color_selector,
    line_width_selector,
    message_level_selector,
    message_search_control,
    page_size_selector,
    plot_selector,
    plot_visibility_toggles,
    polarization_line_width_selector,
    polarization_scale_selector,
    polarization_stride_selector,
    polarization_toggle,
    renderer_toolbar,
    scientific_export_selector,
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
from quantas_gui.explorer.models import (
    PlotFamilyDescriptor,
    PlotSelectionSchema,
    ScientificExportDescriptor,
    ScientificSelectionField,
    TableFamilyDescriptor,
)
from quantas_gui.models.results import EventView, ResultOverview
from quantas_gui.presentation.scientific_labels import scientific_label_text
from quantas_gui.renderers.plotly import PlotDescriptor
from quantas_gui.renderers.tables import table_component


def tables_view(
    families: Sequence[TableFamilyDescriptor],
    *,
    exports: Sequence[ScientificExportDescriptor] = (),
    initial_tables: Sequence[Any] = (),
    initial_groups: Sequence[str] | None = None,
    page_size: int = 50,
) -> html.Div:
    """Create the report-family shell with an optional prepared default family."""
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
                        "Download full table (CSV)",
                        component_id=ResultIds.TABLE_DOWNLOAD,
                        icon="↓",
                    )
                ],
            ),
            html.Div(
                [
                    html.Div(
                        family_note(selected),
                        id=ResultIds.TABLE_FAMILY_INFO,
                    ),
                    html.Small(
                        "The CSV contains the complete selected ReportTable with raw values "
                        "and unit-bearing headers. Grid filters and sorting are visual only.",
                        className="q-table-export-note",
                    ),
                ],
                className="q-table-family-row",
            ),
            dcc.Loading(
                html.Div(
                    rendered_tables_view(
                        initial_tables,
                        page_size=page_size,
                        groups=initial_groups,
                    )
                    if initial_tables
                    else None,
                    id=ResultIds.TABLE_VIEW,
                ),
                type="circle",
                color="#69bce8",
                className="q-result-loading",
            ),
            scientific_export_panel(exports),
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


def plots_view(
    families: Sequence[PlotFamilyDescriptor],
    *,
    initial_schema: PlotSelectionSchema | None = None,
) -> html.Div:
    """Create a lazy plot shell with the default scientific schema prepared."""
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
                    scientific_selection_panel(initial_schema)
                    if initial_schema is not None
                    else None,
                    id=ResultIds.PLOT_SCIENCE_HOST,
                ),
                type="circle",
                color="#69bce8",
                className="q-result-loading",
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
                id=ResultIds.PLOT_ACTIVE_SUMMARY,
                className="q-active-scientific-summary",
                role="status",
            ),
            html.Div(
                id=ResultIds.PLOT_DESCRIPTION,
                className="q-plot-description",
            ),
            html.Div(
                [
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
                                    mathjax=True,
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
                className="q-plot-workbench",
            ),
        ],
        className="q-result-section-stack",
    )


def scientific_selection_panel(schema: PlotSelectionSchema) -> html.Section:
    """Render result-aware scientific choices separately from display controls."""
    fields = tuple(
        field for field in (schema.property_field, *schema.context_fields) if field is not None
    )
    controls = [_scientific_selection_control(field) for field in fields]
    informative = [
        html.Div(
            [
                html.Strong(item.label),
                html.Span(", ".join(item.values) if item.values else "Not available"),
            ],
            className="q-scientific-context-chip",
        )
        for item in schema.informative_contexts
    ]
    notes = [
        html.Li(scientific_label_text(item)) for item in (*schema.constraints, *schema.warnings)
    ]
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Scientific selection", className="q-eyebrow"),
                            html.H3(scientific_label_text(schema.title)),
                            html.P(scientific_label_text(schema.description)),
                        ]
                    ),
                    html.Div(
                        [
                            action_button(
                                "Reset selection",
                                component_id=ResultIds.PLOT_SCIENCE_RESET,
                                icon="↶",
                            ),
                            action_button(
                                "Build selected view",
                                component_id=ResultIds.PLOT_SCIENCE_APPLY,
                                icon="↻",
                                primary=True,
                            ),
                        ],
                        className="q-scientific-selection-actions",
                    ),
                ],
                className="q-scientific-selection-heading",
            ),
            html.Div(
                "Not built yet",
                id=ResultIds.PLOT_SCIENCE_STATUS,
                className="q-scientific-selection-status is-pending",
                role="status",
            ),
            html.Div(controls, className="q-scientific-selection-grid")
            if controls
            else html.P(
                "This representation has no additional scientific choices.",
                className="q-scientific-selection-empty",
            ),
            html.Div(informative, className="q-scientific-context-list") if informative else None,
            html.Details(
                [
                    html.Summary("Scientific constraints and result context"),
                    html.Ul(notes),
                ],
                className="q-scientific-selection-notes",
            )
            if notes
            else None,
        ],
        className="q-panel q-scientific-selection-panel",
    )


def _scientific_selection_control(field: ScientificSelectionField) -> html.Div:
    """Render one property or context selector from exact public values."""
    component_type = (
        ResultIds.PLOT_SCIENCE_PROPERTY
        if field.role == "property"
        else ResultIds.PLOT_SCIENCE_CONTEXT
    )
    dropdown = labelled_dropdown(
        component_id={"type": component_type, "key": field.key},
        label=field.label,
        options=[item.as_option() for item in field.options],
        value=list(field.value) if isinstance(field.value, tuple) else field.value,
        clearable=not field.required,
        searchable=len(field.options) > 8,
        multi=field.multiple,
        class_name="q-control--wide",
    )
    return html.Div(
        [dropdown, html.Small(scientific_label_text(field.description))],
        className="q-scientific-selection-field",
    )


def active_scientific_summary(items: Sequence[str]) -> html.Div:
    """Render the scientific selection that produced the cached PlotCollection."""
    if not items:
        return html.Div()
    return html.Div(
        [
            html.Strong("Built view"),
            html.Div(
                [html.Span(scientific_label_text(item)) for item in items],
                className="q-active-scientific-summary-items",
            ),
        ],
        className="q-active-scientific-summary-content",
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
    """Create a collapsed toolbar grouped by the selected public PlotSpec kind."""
    return html.Details(
        [
            html.Summary(
                [
                    html.Span("Figure controls"),
                    html.Small(
                        "Select a figure",
                        id=ResultIds.PLOT_CONTROL_CONTEXT,
                    ),
                ]
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Small("Presentation changes reuse the cached scientific view."),
                            action_button(
                                "Reset figure appearance",
                                component_id=ResultIds.PLOT_APPEARANCE_RESET,
                                icon="↶",
                            ),
                        ],
                        className="q-plot-appearance-actions",
                    ),
                    _plot_control_section(
                        "Interaction",
                        hover_selector(component_id=ResultIds.PLOT_HOVER),
                        component_id=ResultIds.PLOT_HOVER_WRAP,
                    ),
                    _plot_control_section(
                        "Visibility",
                        plot_visibility_toggles(component_id=ResultIds.PLOT_OPTIONS),
                        component_id=ResultIds.PLOT_DISPLAY_WRAP,
                    ),
                    _plot_control_section(
                        "Lines",
                        [
                            line_width_selector(component_id=ResultIds.PLOT_LINE_WIDTH),
                            line_color_selector(component_id=ResultIds.PLOT_LINE_COLOR),
                        ],
                        component_id=ResultIds.PLOT_LINE_WRAP,
                    ),
                    _plot_control_section(
                        "Colour and scale",
                        [
                            colormap_selector(component_id=ResultIds.PLOT_COLORMAP),
                            colorbar_toggle(component_id=ResultIds.PLOT_COLORBAR),
                        ],
                        component_id=ResultIds.PLOT_COLORMAP_WRAP,
                    ),
                    _plot_control_section(
                        "Contours",
                        [
                            contour_toggles(component_id=ResultIds.PLOT_CONTOUR_OPTIONS),
                            contour_level_control(component_id=ResultIds.PLOT_CONTOUR_LEVELS),
                        ],
                        component_id=ResultIds.PLOT_CONTOUR_WRAP,
                    ),
                    _plot_control_section(
                        "Directional axes",
                        axis_label_mode_selector(component_id=ResultIds.PLOT_AXIS_LABEL_MODE),
                        component_id=ResultIds.PLOT_AXIS_LABEL_WRAP,
                    ),
                    _plot_control_section(
                        "Spherical projection",
                        spherical_projection_selector(component_id=ResultIds.PLOT_PROJECTION),
                        component_id=ResultIds.PLOT_PROJECTION_WRAP,
                    ),
                    _plot_control_section(
                        "Polarization overlays",
                        [
                            polarization_toggle(component_id=ResultIds.PLOT_POLARIZATION),
                            polarization_stride_selector(
                                component_id=ResultIds.PLOT_POLARIZATION_STRIDE
                            ),
                            polarization_line_width_selector(
                                component_id=ResultIds.PLOT_POLARIZATION_WIDTH
                            ),
                            polarization_scale_selector(
                                component_id=ResultIds.PLOT_POLARIZATION_SCALE
                            ),
                            line_color_selector(
                                component_id=ResultIds.PLOT_POLARIZATION_COLOR,
                                label="Polarization colour",
                            ),
                        ],
                        component_id=ResultIds.PLOT_POLARIZATION_WRAP,
                        class_name="q-plot-polarization-controls",
                    ),
                    _plot_control_section(
                        "Three-dimensional view",
                        [
                            surface_opacity_control(component_id=ResultIds.PLOT_SURFACE_OPACITY),
                            camera_selector(component_id=ResultIds.PLOT_CAMERA),
                        ],
                        component_id=ResultIds.PLOT_SURFACE_WRAP,
                        class_name="q-plot-surface-controls",
                    ),
                ],
                className="q-plot-control-sections",
            ),
        ],
        id=ResultIds.PLOT_CONTROL_DRAWER,
        className="q-plot-control-drawer q-panel",
    )


def scientific_export_panel(
    exports: Sequence[ScientificExportDescriptor],
) -> html.Div | html.Details:
    """Create a separate registry-driven area for scientific exports."""
    if not exports:
        return html.Div()
    enabled = any(item.enabled for item in exports)
    return html.Details(
        [
            html.Summary(
                [
                    html.Span("Scientific exports"),
                    html.Small("Public Quantas operations"),
                ]
            ),
            renderer_toolbar(
                [
                    scientific_export_selector(
                        component_id=ResultIds.SCIENTIFIC_EXPORT_SELECTOR,
                        exports=exports,
                    )
                ],
                actions=[
                    action_button(
                        "Run scientific export",
                        component_id=ResultIds.SCIENTIFIC_EXPORT,
                        icon="↓",
                        disabled=not enabled,
                    )
                ],
            ),
            html.Div(
                id=ResultIds.SCIENTIFIC_EXPORT_STATUS,
                className="q-scientific-export-status",
                role="status",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong(item.title),
                            html.P(item.description),
                            html.Small(
                                "Ready"
                                if item.enabled
                                else item.unavailable_reason
                                or "Additional scientific selections are required."
                            ),
                        ],
                        className=(
                            "q-scientific-export-item is-ready"
                            if item.enabled
                            else "q-scientific-export-item is-pending"
                        ),
                    )
                    for item in exports
                ],
                className="q-scientific-export-list",
            ),
        ],
        className="q-scientific-export-panel q-panel",
    )


def _plot_control_section(
    title: str,
    children: Any,
    *,
    component_id: str,
    class_name: str = "",
) -> html.Section:
    content = list(children) if isinstance(children, (list, tuple)) else [children]
    return html.Section(
        [
            html.H4(title),
            html.Div(content, className="q-plot-control-content"),
        ],
        id=component_id,
        className=f"q-plot-control-section {class_name} is-hidden".strip(),
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
