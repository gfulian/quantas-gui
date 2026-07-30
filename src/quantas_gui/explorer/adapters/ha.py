"""Module-aware presentation for harmonic thermodynamics."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter, filter_collection
from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotFamilyDescriptor,
    ScientificExportDescriptor,
)


class HAAdapter(ResultModuleAdapter):
    """Build exact-grid HA representations advertised by Quantas."""

    name = "ha"

    def plot_families(
        self,
        namespace: Any,
        result: Any,
        inventory: Any,
    ) -> tuple[PlotFamilyDescriptor, ...]:
        del namespace, result
        return tuple(
            self._family_from_representation(
                representation,
                default=index == 0,
                cost="low" if representation.plot_kind == "line" else "moderate",
            )
            for index, representation in enumerate(inventory.representations)
        )

    def build_plots(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
        inventory: Any,
        selection: PlotBuildSelection | None = None,
    ) -> Any:
        representation = inventory.representation_by_key(family_key)
        properties = (
            selection.property_keys
            if selection is not None and selection.property_keys
            else tuple(representation.property_keys)
        )
        if family_key == "temperature_curves":
            return namespace.build_plots(
                result,
                properties=properties,
                options=namespace.PlotOptions(
                    curve_axis="temperature",
                    selected_volumes=_selected_floats(selection, "sampled_volume"),
                ),
            )
        if family_key == "volume_curves":
            return namespace.build_plots(
                result,
                properties=properties,
                options=namespace.PlotOptions(
                    curve_axis="volume",
                    selected_temperatures=_selected_floats(selection, "temperature_grid"),
                ),
            )
        if family_key == "volume_temperature_contour":
            collection = namespace.build_plots(
                result,
                properties=properties,
                options=namespace.PlotOptions(include_contours=True),
            )
            return filter_collection(
                collection,
                spec_type_names=("ContourPlotSpec",),
            )
        raise KeyError(f"unknown HA representation {family_key!r}")

    def scientific_exports(
        self,
        namespace: Any,
        result: Any,
        operations: tuple[Any, ...],
    ) -> tuple[ScientificExportDescriptor, ...]:
        """List HA exports while requiring an explicit property selection."""
        del namespace, result
        return tuple(
            ScientificExportDescriptor(
                key=str(operation.key),
                title=str(operation.name),
                description=str(operation.description),
                suffix=".dat",
                enabled=False,
                unavailable_reason="Select the HA property and output unit first.",
            )
            for operation in operations
        )

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        descriptions = {
            "temperature_curves": "exact temperature sections at sampled volumes",
            "volume_curves": "exact volume sections at stored temperatures",
            "volume_temperature_contour": "native volume-temperature map",
        }
        return f"{title}: {descriptions.get(family_key, 'public HA representation')}."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "thermo" in normalized or "heat" in normalized or "entropy" in normalized:
            return "Thermodynamics"
        if "frequency" in normalized or "mode" in normalized:
            return "Vibrations"
        return "HA"


def _selected_floats(
    selection: PlotBuildSelection | None,
    key: str,
) -> tuple[float, ...] | None:
    """Return exact selected native coordinates without interpolation."""
    if selection is None:
        return None
    value = selection.context(key)
    if value is None:
        return None
    values = value if isinstance(value, tuple) else (value,)
    return tuple(float(item) for item in values) or None
