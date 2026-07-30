"""Module-aware presentation for second-order elasticity results."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter
from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotFamilyDescriptor,
    ScientificExportDescriptor,
)


class ElasticityAdapter(ResultModuleAdapter):
    """Expose public polar and three-dimensional elasticity representations."""

    name = "elasticity"

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
                cost="high" if representation.key == "surface_3d" else "low",
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
        if family_key == "polar_2d":
            return namespace.build_2d_plots(result, properties=tuple(properties))
        if family_key == "surface_3d":
            geometry = (
                str(selection.context("surface_geometry", "physical"))
                if selection is not None
                else "physical"
            )
            return namespace.build_3d_plots(
                result,
                options=namespace.SurfaceOptions(properties=tuple(properties)),
                geometry=geometry,
            )
        raise KeyError(f"unknown elasticity representation {family_key!r}")

    def scientific_exports(
        self,
        namespace: Any,
        result: Any,
        operations: tuple[Any, ...],
    ) -> tuple[ScientificExportDescriptor, ...]:
        """Expose the parameter-free public principal-plane table export."""
        del namespace, result
        return tuple(
            ScientificExportDescriptor(
                key=str(operation.key),
                title=str(operation.name),
                description=str(operation.description),
                suffix=".dat",
                enabled=str(operation.key) == "export_2d_table",
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
        """Write the public elasticity table export."""
        if operation_key != "export_2d_table":
            return super().write_scientific_export(namespace, result, operation_key, destination)
        return namespace.write_table(result, destination)

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        if family_key == "polar_2d":
            return f"{title}: public principal-plane directional sections."
        return f"{title}: public directional surface prepared from the stored tensor."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "stiffness" in normalized or "compliance" in normalized:
            return "Tensor"
        if "average" in normalized or "voigt" in normalized or "reuss" in normalized:
            return "Polycrystal"
        if "stability" in normalized:
            return "Stability"
        if "variation" in normalized:
            return "Directional"
        return "Elasticity"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return "2D polar" if family_key == "polar_2d" else "3D surface"
