"""Module-aware presentation for quasi-static thermoelasticity."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter
from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotFamilyDescriptor,
    PlotSelectionSchema,
    ScientificSelectionField,
    ScientificSelectionOption,
    TableFamilyDescriptor,
)


class ThermoelasticityAdapter(ResultModuleAdapter):
    """Expose only public representations supported by the archived stage."""

    name = "thermoelasticity"

    def table_families(self, namespace: Any, result: Any) -> tuple[TableFamilyDescriptor, ...]:
        del namespace, result
        return (
            TableFamilyDescriptor(
                "standard",
                "Standard report",
                "Fit, reconstruction, stability, and provenance summaries.",
                default=True,
            ),
            TableFamilyDescriptor(
                "extended",
                "Extended report",
                "Additional uncertainty and reconstruction details.",
                cost="moderate",
            ),
            TableFamilyDescriptor(
                "debug",
                "Debug report",
                "Detailed fit diagnostics and policy decisions.",
                cost="moderate",
            ),
        )

    def build_tables(self, namespace: Any, result: Any, family_key: str) -> tuple[Any, ...]:
        if family_key not in {"standard", "extended", "debug"}:
            raise KeyError(f"unknown thermoelastic report family {family_key!r}")
        return tuple(namespace.build_report(result, level=family_key))

    def plot_families(
        self,
        namespace: Any,
        result: Any,
        inventory: Any,
    ) -> tuple[PlotFamilyDescriptor, ...]:
        del namespace, result
        families: list[PlotFamilyDescriptor] = []
        for index, representation in enumerate(inventory.representations):
            family = self._family_from_representation(
                representation,
                default=index == 0,
                cost="moderate",
            )
            if family.key == "domain":
                family = replace(
                    family,
                    title="Equilibrium-volume field over the P-T domain",
                    description=(
                        "QHA equilibrium volume V_eq(P,T) used to evaluate the "
                        "calibrated elastic model, with extrapolation masks and "
                        "optional archived depth paths."
                    ),
                )
            families.append(family)
        return tuple(families)

    def plot_selection_schema(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
        inventory: Any,
    ) -> PlotSelectionSchema:
        """Remove duplicate controls while retaining public inventory values."""
        schema = super().plot_selection_schema(namespace, result, family_key, inventory)
        fields = tuple(
            _profile_name_field(field, family_key)
            for field in schema.context_fields
            if field.key not in {"component_group", "pt_quantity", "profile_mode"}
        )
        if family_key == "profile":
            fields += (
                _profile_layout_field(),
                _profile_color_field(),
            )
        property_field = schema.property_field
        if property_field is not None and family_key == "profile":
            property_field = replace(
                property_field,
                multiple=False,
                value=property_field.options[0].value,
            )
        return replace(
            schema,
            property_field=property_field,
            context_fields=fields,
        )

    def build_plots(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
        inventory: Any,
        selection: PlotBuildSelection | None = None,
    ) -> Any:
        inventory.representation_by_key(family_key)
        if family_key == "fit":
            components = _selected_components(selection, "fit_component")
            return namespace.build_fit_plots(result, components=components or None)
        if family_key == "pt":
            components = _selected_components(selection, "stiffness_component")
            property_key = _first_property(selection, "elastic_stiffness")
            quantity = {
                "elastic_stiffness": "value",
                "stiffness_uncertainty": "uncertainty",
                "relative_stiffness_uncertainty": "relative-uncertainty",
            }.get(property_key, "value")
            return namespace.build_pt_plots(
                result,
                components=components or None,
                options=namespace.PTPlotOptions(
                    tensor_condition=str(_context(selection, "pt_tensor_condition", "isothermal")),
                    quantity=quantity,
                ),
            )
        if family_key == "profile":
            names = tuple(inventory.context_by_key("profile_name").values)
            profile_name = (
                str(_context(selection, "profile_name", names[0] if names else "")) or None
            )
            components = _selected_components(selection, "stiffness_component")
            property_key = _first_property(selection, "elastic_stiffness")
            mode = "relative" if property_key == "relative_stiffness_change" else "absolute"
            uncertainty = "band" if property_key == "stiffness_uncertainty" else "auto"
            return namespace.build_profile_plots(
                result,
                profile_name=profile_name,
                components=components or None,
                options=namespace.ProfilePlotOptions(
                    tensor_condition=str(
                        _context(selection, "profile_tensor_condition", "isothermal")
                    ),
                    mode=mode,
                    layout=str(_context(selection, "profile_layout", "overlay")),
                    color_by=str(_context(selection, "profile_color_by", "component")),
                    uncertainty=uncertainty,
                ),
            )
        if family_key == "compare":
            components = _selected_components(selection, "stiffness_component")
            axis = str(_context(selection, "compare_axis", "temperature"))
            if axis == "temperature":
                pressure = float(
                    _context(
                        selection,
                        "compare_fixed_pressure",
                        inventory.context_by_key("compare_fixed_pressure").values[0],
                    )
                )
                options = namespace.ComparePlotOptions(fixed_pressure=pressure)
            else:
                temperature = float(
                    _context(
                        selection,
                        "compare_fixed_temperature",
                        inventory.context_by_key("compare_fixed_temperature").values[0],
                    )
                )
                options = namespace.ComparePlotOptions(fixed_temperature=temperature)
            return namespace.build_compare_plots(
                result, components=components or None, options=options
            )
        if family_key == "domain":
            names = _selected_components(selection, "profile_name")
            collection = namespace.build_domain_plot(result, profile_names=names or None)
            for plot in collection.plots:
                if str(getattr(plot, "key", "")) == "thermoelastic_domain":
                    plot.title = "QHA equilibrium volume over the thermoelastic P-T domain"
            return collection
        raise KeyError(f"unknown thermoelastic representation {family_key!r}")

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        descriptions = {
            "fit": "public elastic-volume calibration and residual diagnostics",
            "pt": "public thermoelastic quantity on the stored P-T grid",
            "profile": "public property evolution along an archived depth path",
            "compare": "public isothermal-adiabatic comparison",
            "domain": (
                "QHA equilibrium volume used by the calibrated elastic model, "
                "including extrapolation coverage and archived depth paths"
            ),
        }
        return f"{title}: {descriptions.get(family_key, 'public thermoelastic representation')}."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "fit" in normalized or "residual" in normalized:
            return "Calibration"
        if "stability" in normalized:
            return "Stability"
        if "profile" in normalized or "depth" in normalized:
            return "Profile"
        if "provenance" in normalized or "metadata" in normalized:
            return "Provenance"
        return "Reconstruction"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return {
            "fit": "Calibration",
            "pt": "P-T map",
            "profile": "Profile",
            "compare": "Comparison",
            "domain": "P-T coverage",
        }.get(family_key, "Thermoelasticity")


def _profile_layout_field() -> ScientificSelectionField:
    """Return public profile-layout choices used during PlotSpec construction."""
    return ScientificSelectionField(
        key="profile_layout",
        label="Component layout",
        description=(
            "Overlay selected C_{ij} on one axis, arrange them as facets, or "
            "return separate figures. This changes presentation, not data."
        ),
        options=(
            ScientificSelectionOption("overlay", "Overlay on one axis"),
            ScientificSelectionOption("facets", "Faceted panels"),
            ScientificSelectionOption("separate", "Separate figures"),
        ),
        value="overlay",
        role="context",
        required=True,
    )


def _profile_color_field() -> ScientificSelectionField:
    """Return public profile colour encodings supported by Quantas."""
    return ScientificSelectionField(
        key="profile_color_by",
        label="Curve colouring",
        description=(
            "Distinguish components by colour, encode the archived temperature "
            "along each path, or use neutral curves."
        ),
        options=(
            ScientificSelectionOption("component", "By stiffness component"),
            ScientificSelectionOption("temperature", "By temperature"),
            ScientificSelectionOption("none", "Neutral curves"),
        ),
        value="component",
        role="context",
        required=True,
    )


def _profile_name_field(field: Any, family_key: str) -> Any:
    """Adapt profile-name cardinality without changing public values."""
    if field.key != "profile_name" or not field.options:
        return field
    if family_key == "domain":
        return replace(
            field,
            multiple=True,
            value=tuple(option.value for option in field.options),
        )
    if family_key == "profile":
        return replace(field, multiple=False, value=field.options[0].value)
    return field


def _context(
    selection: PlotBuildSelection | None,
    key: str,
    default: Any,
) -> Any:
    return default if selection is None else selection.context(key, default)


def _selected_components(
    selection: PlotBuildSelection | None,
    key: str,
) -> tuple[str, ...]:
    if selection is None:
        return ()
    value = selection.context(key)
    if value is None:
        return ()
    values = value if isinstance(value, tuple) else (value,)
    return tuple(str(item) for item in values)


def _first_property(
    selection: PlotBuildSelection | None,
    default: str,
) -> str:
    if selection is None or not selection.property_keys:
        return default
    return str(selection.property_keys[0])
