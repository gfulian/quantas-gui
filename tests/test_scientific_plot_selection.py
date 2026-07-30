from __future__ import annotations

from types import SimpleNamespace

from quantas.api import plotting

from quantas_gui.explorer.adapters import adapter_for
from quantas_gui.explorer.models import PlotBuildSelection


def _inventory() -> plotting.PlotInventory:
    return plotting.PlotInventory(
        module="qha",
        properties=(
            plotting.PlotPropertyDescriptor(
                key="volume",
                name="Equilibrium volume",
                symbol_math=r"$V$",
                symbol_plain="V",
                unit="A^3",
                representations=("temperature_curves",),
            ),
            plotting.PlotPropertyDescriptor(
                key="bulk_modulus",
                name="Isothermal bulk modulus",
                symbol_math=r"$K_T$",
                symbol_plain="K_T",
                unit="GPa",
                representations=("temperature_curves",),
            ),
        ),
        representations=(
            plotting.PlotRepresentationDescriptor(
                key="temperature_curves",
                name="Temperature sections",
                plot_kind="line",
                description="Properties versus temperature at exact stored pressures.",
                property_keys=("volume", "bulk_modulus"),
                supported_contexts=(
                    "curve_axis",
                    "pressure_grid",
                    "calculation_method",
                ),
                constraints=("Only stored pressure coordinates are valid.",),
            ),
        ),
        contexts=(
            plotting.PlotContextDescriptor(
                key="curve_axis",
                name="Curve axis",
                values=("temperature",),
                default="temperature",
            ),
            plotting.PlotContextDescriptor(
                key="pressure_grid",
                name="Pressure sections",
                description="Choose exact stored pressure coordinates.",
                values=(0.0, 5.0, 10.0),
                unit="GPa",
                required=True,
            ),
            plotting.PlotContextDescriptor(
                key="calculation_method",
                name="Calculation method",
                values=("quasi-harmonic",),
                selectable=False,
            ),
        ),
    )


def test_plot_selection_round_trip_and_cache_token_are_stable() -> None:
    selection = PlotBuildSelection(
        family_key="temperature_curves",
        property_keys=("volume",),
        contexts=(("pressure_grid", (0.0, 10.0)), ("show_uncertainty", True)),
    )

    restored = PlotBuildSelection.from_dict(selection.as_dict())

    assert restored == selection
    assert restored is not None
    assert restored.cache_token() == selection.cache_token()
    reversed_contexts = PlotBuildSelection(
        family_key=selection.family_key,
        property_keys=selection.property_keys,
        contexts=tuple(reversed(selection.contexts)),
    )
    assert reversed_contexts.cache_token() == selection.cache_token()


def test_generic_schema_uses_only_public_properties_and_exact_context_values() -> None:
    adapter = adapter_for("qha")
    inventory = _inventory()

    schema = adapter.plot_selection_schema(
        SimpleNamespace(),
        object(),
        "temperature_curves",
        inventory,
    )

    assert schema.property_field is not None
    assert [item.value for item in schema.property_field.options] == [
        "volume",
        "bulk_modulus",
    ]
    assert "V" in schema.property_field.options[0].label
    assert "A³" in schema.property_field.options[0].label
    assert [field.key for field in schema.context_fields] == ["pressure_grid"]
    pressure = schema.context_fields[0]
    assert pressure.multiple
    assert [item.value for item in pressure.options] == [0.0, 5.0, 10.0]
    assert [item.label for item in pressure.options] == [
        "0 GPa",
        "5 GPa",
        "10 GPa",
    ]
    assert [item.key for item in schema.informative_contexts] == ["calculation_method"]
    assert "curve_axis" not in {
        *(field.key for field in schema.context_fields),
        *(item.key for item in schema.informative_contexts),
    }
    assert schema.constraints == ("Only stored pressure coordinates are valid.",)


def test_thermoelastic_profile_names_have_family_specific_cardinality() -> None:
    inventory = plotting.PlotInventory(
        module="thermoelasticity",
        properties=(
            plotting.PlotPropertyDescriptor(
                key="elastic_stiffness",
                name="Elastic stiffness",
                symbol_math=r"$C_{ij}$",
                symbol_plain="C_ij",
                unit="GPa",
                representations=("profile", "domain"),
            ),
        ),
        representations=(
            plotting.PlotRepresentationDescriptor(
                key="profile",
                name="Profile",
                plot_kind="line",
                property_keys=("elastic_stiffness",),
                supported_contexts=("profile_name",),
            ),
            plotting.PlotRepresentationDescriptor(
                key="domain",
                name="Domain",
                plot_kind="contour",
                property_keys=("elastic_stiffness",),
                supported_contexts=("profile_name",),
            ),
        ),
        contexts=(
            plotting.PlotContextDescriptor(
                key="profile_name",
                name="Profile",
                values=("continental", "oceanic"),
                required=True,
            ),
        ),
    )
    adapter = adapter_for("thermoelasticity")

    profile = adapter.plot_selection_schema(SimpleNamespace(), object(), "profile", inventory)
    domain = adapter.plot_selection_schema(SimpleNamespace(), object(), "domain", inventory)

    assert profile.context_fields[0].multiple is False
    assert profile.context_fields[0].value == "continental"
    profile_fields = {field.key: field for field in profile.context_fields}
    assert profile_fields["profile_layout"].value == "overlay"
    assert [item.value for item in profile_fields["profile_layout"].options] == [
        "overlay",
        "facets",
        "separate",
    ]
    assert profile_fields["profile_color_by"].value == "component"
    assert domain.context_fields[0].multiple is True
    assert domain.context_fields[0].value == ("continental", "oceanic")

    families = adapter.plot_families(SimpleNamespace(), object(), inventory)
    domain_family = next(item for item in families if item.key == "domain")
    assert domain_family.title == "Equilibrium-volume field over the P-T domain"
    assert "equilibrium volume" in domain_family.description.lower()


def test_thermoelastic_profile_layout_and_colour_reach_public_options() -> None:
    inventory = plotting.PlotInventory(
        module="thermoelasticity",
        properties=(
            plotting.PlotPropertyDescriptor(
                key="elastic_stiffness",
                name="Elastic stiffness",
                symbol_math=r"$C_{ij}$",
                symbol_plain="C_ij",
                unit="GPa",
                representations=("profile",),
            ),
            plotting.PlotPropertyDescriptor(
                key="relative_stiffness_change",
                name="Relative change",
                symbol_math=r"$\Delta C_{ij}/C_{ij,ref}$",
                symbol_plain="ΔC_ij/C_ij,ref",
                unit="%",
                representations=("profile",),
            ),
        ),
        representations=(
            plotting.PlotRepresentationDescriptor(
                key="profile",
                name="Profile",
                plot_kind="line",
                property_keys=("elastic_stiffness", "relative_stiffness_change"),
                supported_contexts=(
                    "stiffness_component",
                    "profile_name",
                    "profile_tensor_condition",
                ),
            ),
        ),
        contexts=(
            plotting.PlotContextDescriptor(
                key="stiffness_component",
                name="Component",
                values=("C11", "C12"),
                default="C11",
            ),
            plotting.PlotContextDescriptor(
                key="profile_name",
                name="Profile",
                values=("continental",),
            ),
            plotting.PlotContextDescriptor(
                key="profile_tensor_condition",
                name="Condition",
                values=("isothermal", "adiabatic"),
                default="isothermal",
            ),
        ),
    )
    captured: dict[str, object] = {}

    class ProfilePlotOptions:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    namespace = SimpleNamespace(
        ProfilePlotOptions=ProfilePlotOptions,
        build_profile_plots=lambda *args, **kwargs: kwargs,
    )
    selection = PlotBuildSelection(
        family_key="profile",
        property_keys=("relative_stiffness_change",),
        contexts=(
            ("stiffness_component", ("C11", "C12")),
            ("profile_name", "continental"),
            ("profile_tensor_condition", "adiabatic"),
            ("profile_layout", "overlay"),
            ("profile_color_by", "component"),
        ),
    )

    adapter_for("thermoelasticity").build_plots(
        namespace,
        object(),
        "profile",
        inventory,
        selection,
    )

    assert captured["mode"] == "relative"
    assert captured["tensor_condition"] == "adiabatic"
    assert captured["layout"] == "overlay"
    assert captured["color_by"] == "component"


def test_long_informative_coordinate_grids_are_summarized() -> None:
    temperatures = tuple(float(value) for value in range(300, 401, 10))
    inventory = plotting.PlotInventory(
        module="qha",
        properties=(
            plotting.PlotPropertyDescriptor(
                key="volume",
                name="Equilibrium volume",
                symbol_math=r"$V$",
                symbol_plain="V",
                unit="A^3",
                representations=("pt_map",),
            ),
        ),
        representations=(
            plotting.PlotRepresentationDescriptor(
                key="pt_map",
                name="P-T map",
                plot_kind="contour",
                property_keys=("volume",),
                supported_contexts=("temperature_grid",),
            ),
        ),
        contexts=(
            plotting.PlotContextDescriptor(
                key="temperature_grid",
                name="Stored temperature grid",
                values=temperatures,
                unit="K",
            ),
        ),
    )

    schema = adapter_for("qha").plot_selection_schema(
        SimpleNamespace(), object(), "pt_map", inventory
    )

    assert schema.context_fields == ()
    assert len(schema.informative_contexts) == 1
    assert schema.informative_contexts[0].values == ("300 K to 400 K · 11 points · step 10 K",)
