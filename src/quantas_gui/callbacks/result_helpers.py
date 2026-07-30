"""Pure helpers shared by Results Explorer callback modules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import plotly.graph_objects as go

from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotSelectionSchema,
    ScientificSelectionField,
    ScientificSelectionValue,
)
from quantas_gui.models.results import (
    ActiveResultState,
    ResultOverview,
    ResultReference,
    ResultSummary,
)


def result_session_data(
    reference: ResultReference,
    overview: ResultOverview,
) -> dict[str, Any]:
    """Return the lightweight global active-result payload."""
    return ActiveResultState(reference=reference, summary=overview.summary).as_dict()


def reference_from_session(session: dict[str, Any]) -> ResultReference:
    """Restore the opaque active result reference from browser state."""
    return ActiveResultState.from_dict(session).reference


def summary_from_session(session: dict[str, Any]) -> ResultSummary:
    """Restore the lightweight active result summary from browser state."""
    return ActiveResultState.from_dict(session).summary


def plot_build_selection(
    family_key: str,
    property_values: Sequence[Any],
    property_ids: Sequence[Any],
    context_values: Sequence[Any],
    context_ids: Sequence[Any],
) -> PlotBuildSelection:
    """Normalize native Dash selector values into lightweight scientific state."""
    properties: list[str] = []
    for value, identifier in zip(property_values, property_ids, strict=True):
        if not identifier:
            continue
        values = value if isinstance(value, list) else [value]
        properties.extend(str(item) for item in values if item is not None)

    contexts: list[tuple[str, ScientificSelectionValue]] = []
    for value, identifier in zip(context_values, context_ids, strict=True):
        if not isinstance(identifier, dict) or "key" not in identifier:
            continue
        if value in (None, []):
            continue
        normalized: ScientificSelectionValue = tuple(value) if isinstance(value, list) else value
        contexts.append((str(identifier["key"]), normalized))

    return PlotBuildSelection(
        family_key=str(family_key),
        property_keys=tuple(dict.fromkeys(properties)),
        contexts=tuple(contexts),
    )


def selection_summary(
    schema: PlotSelectionSchema,
    selection: PlotBuildSelection,
) -> tuple[str, ...]:
    """Return concise labels describing the built scientific selection."""
    items: list[str] = []
    if schema.property_field is not None:
        items.extend(_selected_labels(schema.property_field, selection.property_keys))
    selected_contexts = dict(selection.contexts)
    for field in schema.context_fields:
        value = selected_contexts.get(field.key)
        labels = _selected_labels(field, value)
        if labels:
            items.append(f"{field.label}: {', '.join(labels)}")
    return tuple(items)


def default_selector_values(
    schema: PlotSelectionSchema,
    property_ids: Sequence[Any],
    context_ids: Sequence[Any],
) -> tuple[list[Any], list[Any]]:
    """Return schema defaults in the exact order of dynamic Dash component IDs."""
    fields = {
        field.key: field
        for field in (schema.property_field, *schema.context_fields)
        if field is not None
    }
    properties = [_field_dash_value(fields.get(_identifier_key(item))) for item in property_ids]
    contexts = [_field_dash_value(fields.get(_identifier_key(item))) for item in context_ids]
    return properties, contexts


def plot_control_configuration(
    controls: dict[str, Any],
) -> tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    list[dict[str, str]],
    list[str],
]:
    """Return plot-kind section classes and visibility-toggle options."""

    def section_class(active: bool, modifier: str = "") -> str:
        classes = ["q-plot-control-section"]
        if modifier:
            classes.append(modifier)
        if not active:
            classes.append("is-hidden")
        return " ".join(classes)

    visibility = [("legend", "Legend"), ("grid", "Grid"), ("axes", "Axes")]
    visibility_options = [
        {"label": label, "value": key} for key, label in visibility if bool(controls.get(key))
    ]
    visibility_values = [str(item["value"]) for item in visibility_options]
    return (
        section_class(bool(controls.get("hover", False))),
        section_class(bool(visibility_options)),
        section_class(bool(controls.get("line_style"))),
        section_class(bool(controls.get("colormap") or controls.get("colorbar"))),
        section_class(bool(controls.get("axis_labels"))),
        section_class(bool(controls.get("projection"))),
        section_class(bool(controls.get("contour"))),
        section_class(bool(controls.get("polarization")), "q-plot-polarization-controls"),
        section_class(bool(controls.get("surface")), "q-plot-surface-controls"),
        visibility_options,
        visibility_values,
    )


def plot_kind_label(kind: str) -> str:
    """Return one compact public PlotSpec label."""
    return {
        "LinePlotSpec": "Line plot",
        "ContourPlotSpec": "Contour map",
        "PolarPlotSpec": "Polar plot",
        "SurfacePlotSpec": "3D surface",
        "SphericalMapSpec": "Spherical map",
        "SphericalSummarySpec": "Spherical summary",
        "PanelPlotSpec": "Panel figure",
    }.get(kind, kind.removesuffix("PlotSpec") or "Figure")


def source_optional_string(value: Any) -> str | None:
    """Return ``None`` for the source-preserving selector sentinel."""
    return None if value in (None, "source") else str(value)


def source_optional_float(value: Any) -> float | None:
    """Return a float override or preserve the public source style."""
    return None if value in (None, "source") else float(value)


def safe_filename(value: str) -> str:
    """Return one bounded derived filename stem."""
    cleaned = "".join(character if character.isalnum() else "-" for character in value.lower())
    return "-".join(part for part in cleaned.split("-") if part) or "quantas-table"


def empty_figure(message: str, *, theme: str = "dark") -> go.Figure:
    """Create a theme-aware placeholder figure."""
    figure = go.Figure()
    light = theme == "light"
    figure.update_layout(
        paper_bgcolor="#ffffff" if light else "#0d2030",
        plot_bgcolor="#f7fafc" if light else "#071522",
        font={"color": "#10283a" if light else "#ecf5fb"},
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {
                    "color": "#5f7482" if light else "#b3c7d5",
                    "size": 14,
                },
            }
        ],
    )
    return figure


def _selected_labels(
    field: ScientificSelectionField,
    selected: Any,
) -> list[str]:
    values = selected if isinstance(selected, (list, tuple)) else (selected,)
    labels = {option.value: option.label for option in field.options}
    return [labels.get(value, str(value)) for value in values if value is not None]


def _identifier_key(identifier: Any) -> str:
    if isinstance(identifier, dict):
        return str(identifier.get("key", ""))
    return ""


def _field_dash_value(field: ScientificSelectionField | None) -> Any:
    if field is None:
        return None
    return list(field.value) if isinstance(field.value, tuple) else field.value
