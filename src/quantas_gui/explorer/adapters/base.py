"""Base module adapter for the Results Explorer.

Adapters consume only public ``quantas.api`` namespaces and result-aware plot
inventories. They may organize the interface, but they never infer scientific
availability from implementation payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from quantas_gui.explorer.models import (
    ArtifactCost,
    InformativeScientificContext,
    PlotBuildSelection,
    PlotFamilyDescriptor,
    PlotSelectionSchema,
    ScientificExportDescriptor,
    ScientificSelectionField,
    ScientificSelectionOption,
    ScientificSelectionValue,
    TableFamilyDescriptor,
)
from quantas_gui.presentation.scientific_labels import scientific_label_text


@dataclass(slots=True)
class GuiPlotCollection:
    """Small structural PlotCollection used when a public API returns one spec."""

    plots: list[Any]
    warnings: list[str]


class ResultModuleAdapter:
    """Generic public-API adapter for result presentation."""

    name = "generic"

    def table_families(
        self,
        namespace: Any,
        result: Any,
    ) -> tuple[TableFamilyDescriptor, ...]:
        """Return report families supported by this result."""
        del namespace, result
        return (
            TableFamilyDescriptor(
                key="default",
                title="Report",
                description="Frontend-neutral report tables exposed by Quantas.",
                default=True,
            ),
        )

    def build_tables(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
    ) -> tuple[Any, ...]:
        """Build one report family."""
        if family_key != "default":
            raise KeyError(f"unknown report family {family_key!r}")
        return tuple(namespace.build_report(result))

    def plot_families(
        self,
        namespace: Any,
        result: Any,
        inventory: Any,
    ) -> tuple[PlotFamilyDescriptor, ...]:
        """Translate public representation descriptors into GUI families."""
        del namespace, result
        return tuple(
            self._family_from_representation(item, default=index == 0)
            for index, item in enumerate(inventory.representations)
        )

    def plot_selection_schema(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
        inventory: Any,
    ) -> PlotSelectionSchema:
        """Build scientific selectors strictly from one public plot inventory."""
        del namespace, result
        representation = inventory.representation_by_key(family_key)
        properties = tuple(inventory.property_by_key(key) for key in representation.property_keys)
        property_field = _property_field(representation, properties)
        context_fields: list[ScientificSelectionField] = []
        informative: list[InformativeScientificContext] = []
        for key in representation.supported_contexts:
            if str(key) == "curve_axis":
                continue
            context = inventory.context_by_key(key)
            if _context_is_informative(representation, context):
                informative.append(_informative_context(context))
                continue
            context_fields.append(_context_field(representation, context))
        return PlotSelectionSchema(
            family_key=family_key,
            title=str(representation.name),
            description=str(representation.description),
            property_field=property_field,
            context_fields=tuple(context_fields),
            informative_contexts=tuple(informative),
            constraints=tuple(str(item) for item in representation.constraints),
            warnings=tuple(str(item) for item in inventory.warnings),
        )

    def default_plot_selection(
        self,
        schema: PlotSelectionSchema,
    ) -> PlotBuildSelection:
        """Return the lightweight default represented by one selection schema."""
        property_keys: tuple[str, ...] = ()
        field = schema.property_field
        if field is not None:
            property_keys = _selection_tuple(field.value)
        contexts = tuple((field.key, field.value) for field in schema.context_fields)
        return PlotBuildSelection(
            family_key=schema.family_key,
            property_keys=property_keys,
            contexts=contexts,
        )

    def build_plots(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
        inventory: Any,
        selection: PlotBuildSelection | None = None,
    ) -> Any:
        """Build one generic plot family through the public default builder."""
        del selection
        inventory.representation_by_key(family_key)
        return namespace.build_plots(result)

    def scientific_exports(
        self,
        namespace: Any,
        result: Any,
        operations: tuple[Any, ...],
    ) -> tuple[ScientificExportDescriptor, ...]:
        """Describe public exports without inventing operation parameters."""
        del namespace, result
        return tuple(
            ScientificExportDescriptor(
                key=str(operation.key),
                title=str(operation.name),
                description=str(operation.description),
                suffix=".dat",
                enabled=False,
                unavailable_reason=("This export requires module-specific scientific selections."),
            )
            for operation in operations
        )

    def write_scientific_export(
        self,
        namespace: Any,
        result: Any,
        operation_key: str,
        destination: Any,
    ) -> Any:
        """Write one configured public export."""
        del namespace, result, destination
        raise ValueError(
            f"scientific export {operation_key!r} requires module-specific configuration"
        )

    def table_group(self, title: str) -> str:
        """Return a compact table-group label."""
        del title
        return "Report"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        """Return a compact plot-group label."""
        del title, family_key
        return _kind_label(kind)

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        """Return a short plot explanation."""
        del family_key
        return f"{title} rendered from a frontend-neutral {kind}."

    @staticmethod
    def _family_from_representation(
        representation: Any,
        *,
        default: bool,
        cost: ArtifactCost | None = None,
    ) -> PlotFamilyDescriptor:
        """Create one GUI family without copying scientific catalogues."""
        resolved_cost: ArtifactCost = cost or (
            "high" if representation.plot_kind == "surface" else "moderate"
        )
        return PlotFamilyDescriptor(
            key=str(representation.key),
            title=str(representation.name),
            description=str(representation.description),
            default=default,
            cost=resolved_cost,
            icon=_kind_icon(str(representation.plot_kind)),
            plot_kind=str(representation.plot_kind),
            property_keys=tuple(str(item) for item in representation.property_keys),
            supported_contexts=tuple(str(item) for item in representation.supported_contexts),
            constraints=tuple(str(item) for item in representation.constraints),
        )


def filter_collection(
    collection: Any,
    *,
    spec_type_names: tuple[str, ...],
) -> GuiPlotCollection:
    """Filter a public collection using public PlotSpec classes."""
    plotting = import_module("quantas.api.plotting")
    spec_types = tuple(getattr(plotting, name) for name in spec_type_names)
    return GuiPlotCollection(
        plots=[item for item in collection.plots if isinstance(item, spec_types)],
        warnings=[str(item) for item in collection.warnings],
    )


_GRID_CONTEXT_KEYS = frozenset({"temperature_grid", "pressure_grid", "sampled_volume"})
_MULTI_CONTEXT_KEYS = frozenset(
    {
        "temperature_grid",
        "pressure_grid",
        "sampled_volume",
        "wave_mode",
        "surface_type",
        "stiffness_component",
        "fit_component",
    }
)


def _property_field(
    representation: Any,
    properties: tuple[Any, ...],
) -> ScientificSelectionField | None:
    """Create a property selector when the representation has a real choice."""
    if len(properties) <= 1 or str(representation.key) == "spherical_summary":
        return None
    multiple = str(representation.plot_kind) in {"line", "polar", "panel"}
    options = tuple(
        ScientificSelectionOption(
            value=str(item.key),
            label=_property_label(item),
            description=str(item.description),
        )
        for item in properties
    )
    default: ScientificSelectionValue = (
        (str(properties[0].key),) if multiple else str(properties[0].key)
    )
    return ScientificSelectionField(
        key="properties",
        label="Scientific property" if not multiple else "Scientific properties",
        description="Select only quantities advertised for this representation by Quantas.",
        options=options,
        value=default,
        role="property",
        multiple=multiple,
        required=True,
    )


def _property_label(item: Any) -> str:
    """Return a compact native-dropdown label with quantity and unit."""
    symbol = scientific_label_text(str(item.symbol_plain or item.symbol_math))
    unit = scientific_label_text(str(item.unit)) if item.unit else ""
    suffix = f" ({unit})" if unit else ""
    return f"{symbol} · {item.name}{suffix}"


def _context_is_informative(representation: Any, context: Any) -> bool:
    """Return whether a context describes the result but does not rebuild it."""
    if not bool(context.selectable):
        return True
    key = str(context.key)
    return str(representation.plot_kind) == "contour" and key in _GRID_CONTEXT_KEYS


def _context_field(representation: Any, context: Any) -> ScientificSelectionField:
    """Translate one exact public context into a generic scientific selector."""
    key = str(context.key)
    multiple = key in _MULTI_CONTEXT_KEYS and (
        key not in _GRID_CONTEXT_KEYS or str(representation.plot_kind) == "line"
    )
    options = tuple(
        ScientificSelectionOption(
            value=value,
            label=_context_value_label(value, context.unit),
        )
        for value in context.values
    )
    value = _context_default(context, multiple=multiple)
    return ScientificSelectionField(
        key=key,
        label=str(context.name),
        description=str(context.description),
        options=options,
        value=value,
        role="context",
        multiple=multiple,
        required=bool(context.required),
        unit=str(context.unit) if context.unit else None,
    )


def _context_default(context: Any, *, multiple: bool) -> ScientificSelectionValue:
    """Choose exact inventory values without interpolation or scientific inference."""
    values = tuple(context.values)
    if context.default is not None:
        return (context.default,) if multiple else context.default
    if not values:
        return () if multiple else None
    if multiple:
        key = str(context.key)
        if key in _GRID_CONTEXT_KEYS:
            if len(values) <= 6:
                return values
            indices = (0, len(values) // 2, len(values) - 1)
            return tuple(values[index] for index in dict.fromkeys(indices))
        return values
    if False in values:
        return False
    return values[0]


def _context_value_label(value: Any, unit: Any) -> str:
    """Format one exact context coordinate for a native Dash selector."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = scientific_label_text(str(value).replace("_", " "))
    if unit:
        text = f"{text} {scientific_label_text(str(unit))}"
    return text


def _informative_context(context: Any) -> InformativeScientificContext:
    """Translate one non-editable public context into compact display metadata."""
    key = str(context.key)
    raw_values = tuple(context.values)
    values: tuple[str, ...]
    if key in _GRID_CONTEXT_KEYS and len(raw_values) > 6:
        values = (_numeric_grid_summary(raw_values, context.unit),)
    else:
        values = tuple(_context_value_label(value, context.unit) for value in raw_values)
    return InformativeScientificContext(
        key=key,
        label=str(context.name),
        values=values,
        unit=str(context.unit) if context.unit else None,
    )


def _numeric_grid_summary(values: tuple[Any, ...], unit: Any) -> str:
    """Summarize a long exact numeric grid without moving it into browser state."""
    try:
        numeric = tuple(float(value) for value in values)
    except (TypeError, ValueError):
        return f"{len(values)} stored values"
    first = _context_value_label(numeric[0], unit)
    last = _context_value_label(numeric[-1], unit)
    differences = tuple(numeric[index + 1] - numeric[index] for index in range(len(numeric) - 1))
    regular = bool(differences) and max(differences) - min(differences) <= max(
        1.0e-12, abs(differences[0]) * 1.0e-10
    )
    if regular:
        step = _context_value_label(differences[0], unit)
        return f"{first} to {last} · {len(numeric)} points · step {step}"
    return f"{first} to {last} · {len(numeric)} stored points"


def _selection_tuple(value: ScientificSelectionValue) -> tuple[str, ...]:
    """Normalize one property selector value to stable string keys."""
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    return (str(value),)


def _kind_icon(kind: str) -> str:
    return {
        "line": "∿",
        "contour": "▦",
        "polar": "◉",
        "spherical_map": "◉",
        "spherical_summary": "⌖",
        "surface": "⬡",
        "panel": "▤",
    }.get(kind, "◇")


def _kind_label(kind: str) -> str:
    return {
        "LinePlotSpec": "Line",
        "ContourPlotSpec": "Contour",
        "PolarPlotSpec": "Polar",
        "SurfacePlotSpec": "3D surface",
        "SphericalMapSpec": "Spherical map",
        "SphericalSummarySpec": "Spherical summary",
        "PanelPlotSpec": "Panels",
    }.get(kind, kind.removesuffix("PlotSpec") or "Plot")


__all__ = ["GuiPlotCollection", "ResultModuleAdapter", "filter_collection"]
