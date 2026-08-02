"""Module-aware presentation for directional seismic results."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from quantas_gui.explorer.adapters.base import GuiPlotCollection, ResultModuleAdapter
from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotFamilyDescriptor,
    PlotSelectionSchema,
    ScientificExportDescriptor,
    TableFamilyDescriptor,
)


class SeismicAdapter(ResultModuleAdapter):
    """Present the public seismic inventory without duplicating its catalogue."""

    name = "seismic"

    def table_families(self, namespace: Any, result: Any) -> tuple[TableFamilyDescriptor, ...]:
        del namespace, result
        return (
            TableFamilyDescriptor(
                "standard",
                "Standard report",
                "Compact isotropic values, extrema, and anisotropy summaries.",
            ),
            TableFamilyDescriptor(
                "extended",
                "Extended report",
                "Wave-property tables and detailed directional extrema.",
                default=True,
                cost="moderate",
            ),
            TableFamilyDescriptor(
                "debug",
                "Debug report",
                "Numerical diagnostics, degeneracies, and enhancement details.",
                cost="moderate",
            ),
        )

    def build_tables(self, namespace: Any, result: Any, family_key: str) -> tuple[Any, ...]:
        if family_key not in {"standard", "extended", "debug"}:
            raise KeyError(f"unknown SEISMIC report family {family_key!r}")
        return tuple(namespace.build_report(result, level=family_key))

    def plot_families(
        self,
        namespace: Any,
        result: Any,
        inventory: Any,
    ) -> tuple[PlotFamilyDescriptor, ...]:
        del namespace, result
        families = tuple(
            self._family_from_representation(
                representation,
                default=index == 0,
                cost="high" if representation.plot_kind == "surface" else "moderate",
            )
            for index, representation in enumerate(inventory.representations)
        )
        return tuple(_present_surface_family(family) for family in families)

    def plot_selection_schema(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
        inventory: Any,
    ) -> PlotSelectionSchema:
        """Clarify SEISMIC surface choices without changing public availability."""
        schema = super().plot_selection_schema(namespace, result, family_key, inventory)
        if family_key == "property_surface_3d":
            property_field = schema.property_field
            if property_field is not None:
                default = (
                    property_field.value
                    if isinstance(property_field.value, tuple)
                    else (() if property_field.value is None else (property_field.value,))
                )
                property_field = replace(
                    property_field,
                    label="Scalar properties",
                    description=(
                        "Select one or more scalar fields, build them together, then switch "
                        "immediately between the generated figures. Use the dedicated "
                        "Acoustic wave surface for canonical phase, slowness and group "
                        "surfaces."
                    ),
                    value=default,
                    multiple=True,
                )
            return replace(
                schema,
                title="General scalar-field surface",
                description=(
                    "Directional scalar fields on a unit sphere or their natural physical "
                    "carrier. This family is especially useful for anisotropy, shear "
                    "splitting, velocity ratios, power-flow angle and enhancement."
                ),
                property_field=property_field,
            )
        if family_key == "acoustic_surface_3d":
            return replace(
                schema,
                title="Acoustic wave surface",
                description=(
                    "Canonical phase-velocity, slowness or group-wavefront surfaces selected "
                    "by acoustic mode. Select several types and modes, build once, then "
                    "switch immediately between the generated figures."
                ),
            )
        return schema

    def build_plots(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
        inventory: Any,
        selection: PlotBuildSelection | None = None,
    ) -> Any:
        representation = inventory.representation_by_key(family_key)
        available_polarizations = _polarization_overlay_available(inventory)
        include_polarizations = available_polarizations and (
            True if selection is None else bool(selection.context("polarization_overlay", False))
        )
        projection = str(_context(selection, "projection", "equal_area"))
        extrema = bool(_context(selection, "extrema_markers", True))
        properties = (
            selection.property_keys
            if selection is not None and selection.property_keys
            else tuple(representation.property_keys)
        )
        if family_key == "spherical_map":
            return namespace.build_plots(
                result,
                options=namespace.PlotOptions(
                    properties=tuple(properties),
                    projection=projection,
                    include_extrema_markers=extrema,
                    include_polarizations=include_polarizations,
                    polarization_stride=1,
                ),
            )
        if family_key == "spherical_summary":
            return GuiPlotCollection(
                plots=[
                    namespace.build_summary(
                        result,
                        options=namespace.PlotOptions(
                            projection=projection,
                            include_extrema_markers=extrema,
                            include_polarizations=include_polarizations,
                            polarization_stride=1,
                        ),
                    )
                ],
                warnings=[],
            )
        geometry = str(_context(selection, "surface_geometry", "unit_sphere"))
        antipodal = bool(_context(selection, "antipodal_completion", True))
        if family_key == "property_surface_3d":
            return namespace.build_surfaces(
                result,
                options=namespace.SurfaceOptions(
                    properties=tuple(properties),
                    geometry=geometry,
                    complete_antipodal_surface=antipodal,
                    include_polarizations=include_polarizations,
                    polarization_stride=1,
                ),
            )
        if family_key == "acoustic_surface_3d":
            surface_types = _tuple_strings(
                _context(
                    selection,
                    "surface_type",
                    _inventory_values(inventory, "surface_type", ("phase",)),
                )
            )
            modes = _tuple_strings(
                _context(
                    selection,
                    "wave_mode",
                    _inventory_values(inventory, "wave_mode", ("v_p", "v_s1", "v_s2")),
                )
            )
            return namespace.build_surfaces(
                result,
                options=namespace.SurfaceOptions(
                    surface_types=surface_types,
                    modes=modes,
                    geometry=geometry,
                    complete_antipodal_surface=antipodal,
                    include_polarizations=include_polarizations,
                    polarization_stride=1,
                ),
            )
        raise KeyError(f"unknown SEISMIC representation {family_key!r}")

    def scientific_exports(
        self,
        namespace: Any,
        result: Any,
        operations: tuple[Any, ...],
    ) -> tuple[ScientificExportDescriptor, ...]:
        """Expose the parameter-free public directional CSV export."""
        del namespace, result
        return tuple(
            ScientificExportDescriptor(
                key=str(operation.key),
                title=str(operation.name),
                description=str(operation.description),
                suffix=".csv",
                enabled=str(operation.key) == "export_csv",
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
        """Write the public SEISMIC directional CSV export."""
        if operation_key != "export_csv":
            return super().write_scientific_export(namespace, result, operation_key, destination)
        return namespace.write_csv(result, destination)

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        descriptions = {
            "spherical_map": "directional scalar field on the public spherical projection",
            "spherical_summary": "public extrema, directions, and anisotropy summary",
            "property_surface_3d": (
                "general directional scalar field on a unit sphere or natural physical carrier"
            ),
            "acoustic_surface_3d": (
                "canonical phase-velocity, slowness, or group-wavefront surface by wave mode"
            ),
        }
        return f"{title}: {descriptions.get(family_key, 'public seismic representation')}."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "isotropic" in normalized:
            return "Reference"
        if "extrem" in normalized or "anisotrop" in normalized:
            return "Directional"
        if "degener" in normalized or "caustic" in normalized or "enhancement" in normalized:
            return "Diagnostics"
        return "Wave field"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return {
            "spherical_map": "Spherical map",
            "spherical_summary": "Summary",
            "property_surface_3d": "Scalar fields",
            "acoustic_surface_3d": "Acoustic waves",
        }.get(family_key, "SEISMIC")


def _present_surface_family(family: PlotFamilyDescriptor) -> PlotFamilyDescriptor:
    """Return clearer GUI labels for the two public SEISMIC surface families."""
    if family.key == "property_surface_3d":
        return replace(
            family,
            title="General scalar-field surface",
            description=(
                "Build one or more directional scalar fields together. Prefer this family "
                "for anisotropy, shear splitting, velocity ratios, power-flow angle and "
                "enhancement."
            ),
        )
    if family.key == "acoustic_surface_3d":
        return replace(
            family,
            title="Acoustic wave surface",
            description=(
                "Build canonical phase-velocity, slowness and group-wavefront surfaces by "
                "acoustic mode."
            ),
        )
    return family


def _polarization_overlay_available(inventory: Any) -> bool:
    """Return whether the public inventory advertises tracked axes."""
    try:
        values = inventory.context_by_key("polarization_overlay").values
    except (AttributeError, KeyError, ValueError):
        return False
    return any(value is True for value in values)


def _context(
    selection: PlotBuildSelection | None,
    key: str,
    default: Any,
) -> Any:
    return default if selection is None else selection.context(key, default)


def _tuple_strings(value: Any) -> tuple[str, ...]:
    values = value if isinstance(value, tuple) else (value,)
    return tuple(str(item) for item in values)


def _inventory_values(
    inventory: Any,
    key: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    try:
        return tuple(str(item) for item in inventory.context_by_key(key).values)
    except (AttributeError, KeyError, ValueError):
        return default
