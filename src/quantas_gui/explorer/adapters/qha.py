"""Module-aware presentation for quasi-harmonic thermodynamics."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter, filter_collection
from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotFamilyDescriptor,
    ScientificExportDescriptor,
)


class QHAAdapter(ResultModuleAdapter):
    """Build exact native-grid QHA sections and maps from public descriptors."""

    name = "qha"

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
                cost="moderate",
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
                    include_contours=False,
                    selected_pressures=_selected_floats(selection, "pressure_grid"),
                ),
            )
        if family_key == "pressure_curves":
            return namespace.build_plots(
                result,
                properties=properties,
                options=namespace.PlotOptions(
                    curve_axis="pressure",
                    include_contours=False,
                    selected_temperatures=_selected_floats(selection, "temperature_grid"),
                ),
            )
        if family_key == "pressure_temperature_contour":
            collection = namespace.build_plots(
                result,
                properties=properties,
                options=namespace.PlotOptions(include_contours=True),
            )
            return filter_collection(
                collection,
                spec_type_names=("ContourPlotSpec",),
            )
        raise KeyError(f"unknown QHA representation {family_key!r}")

    def scientific_exports(
        self,
        namespace: Any,
        result: Any,
        operations: tuple[Any, ...],
    ) -> tuple[ScientificExportDescriptor, ...]:
        """Expose the public all-properties pressure-temperature CSV export."""
        del namespace, result
        return tuple(
            ScientificExportDescriptor(
                key=str(operation.key),
                title=str(operation.name),
                description=str(operation.description),
                suffix=".csv",
                enabled=str(operation.key) == "export_pt_table",
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
        """Write the public QHA all-properties CSV export."""
        if operation_key != "export_pt_table":
            return super().write_scientific_export(namespace, result, operation_key, destination)
        return namespace.write_table(
            result,
            destination,
            property_name=None,
            include_uncertainty=True,
            file_format="csv",
        )

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        descriptions = {
            "temperature_curves": "exact temperature sections at stored pressures",
            "pressure_curves": "exact pressure sections at stored temperatures",
            "pressure_temperature_contour": "native pressure-temperature map",
        }
        return f"{title}: {descriptions.get(family_key, 'public QHA representation')}."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "equilibrium" in normalized or "volume" in normalized or "density" in normalized:
            return "Equilibrium"
        if "fit" in normalized or "residual" in normalized or "diagnostic" in normalized:
            return "Fit diagnostics"
        if "grüneisen" in normalized or "gruneisen" in normalized:
            return "Grüneisen"
        return "Thermodynamics"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return {
            "temperature_curves": "Temperature section",
            "pressure_curves": "Pressure section",
            "pressure_temperature_contour": "P-T contour",
        }.get(family_key, "QHA")


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
