from __future__ import annotations

from types import SimpleNamespace

from quantas.api import plotting

from quantas_gui.explorer.adapters import adapter_for, registered_adapters
from quantas_gui.explorer.models import PlotBuildSelection


def test_all_scientific_result_adapters_are_registered() -> None:
    assert set(registered_adapters()) == {
        "elasticity",
        "seismic",
        "ha",
        "qha",
        "thermoelasticity",
        "eos",
    }


def test_elasticity_uses_public_representation_inventory_without_building() -> None:
    inventory = plotting.PlotInventory(
        module="elasticity",
        properties=(
            plotting.PlotPropertyDescriptor(
                key="young",
                name="Young modulus",
                symbol_math="E",
                symbol_plain="E",
                unit="GPa",
                representations=("polar_2d", "surface_3d"),
            ),
        ),
        representations=(
            plotting.PlotRepresentationDescriptor(
                key="polar_2d",
                name="Principal-plane polar sections",
                plot_kind="polar",
                property_keys=("young",),
            ),
            plotting.PlotRepresentationDescriptor(
                key="surface_3d",
                name="Directional surfaces",
                plot_kind="surface",
                property_keys=("young",),
            ),
        ),
    )
    namespace = SimpleNamespace()
    result = object()
    families = adapter_for("elasticity").plot_families(namespace, result, inventory)
    assert [(item.key, item.cost) for item in families] == [
        ("polar_2d", "low"),
        ("surface_3d", "high"),
    ]
    assert families[0].property_keys == ("young",)


def test_eos_remains_outside_generic_one_shot_plot_families() -> None:
    assert adapter_for("eos").plot_families(object(), object(), object()) == ()


def test_scientific_exports_follow_module_specific_public_contracts(tmp_path) -> None:
    operations = (
        SimpleNamespace(
            key="export_2d_table",
            name="Export 2D table",
            description="Write directional data.",
        ),
    )
    elasticity = adapter_for("elasticity")
    descriptors = elasticity.scientific_exports(SimpleNamespace(), object(), operations)
    assert descriptors[0].enabled
    assert descriptors[0].suffix == ".dat"

    destination = tmp_path / "elasticity.dat"
    calls = []
    namespace = SimpleNamespace(
        write_table=lambda result, path: calls.append((result, path)) or path
    )
    result = object()
    assert (
        elasticity.write_scientific_export(
            namespace,
            result,
            "export_2d_table",
            destination,
        )
        == destination
    )
    assert calls == [(result, destination)]


def test_ha_scientific_export_requires_property_selection() -> None:
    operation = SimpleNamespace(
        key="export_property_table",
        name="Export HA property table",
        description="Write one harmonic property.",
    )
    descriptor = adapter_for("ha").scientific_exports(
        SimpleNamespace(),
        object(),
        (operation,),
    )[0]
    assert not descriptor.enabled
    assert "property" in str(descriptor.unavailable_reason).lower()


def test_seismic_builders_request_public_polarization_layers_when_available() -> None:
    calls: list[tuple[str, object]] = []

    class Options:
        def __init__(self, **values):
            self.__dict__.update(values)

    representations = {
        "spherical_map": SimpleNamespace(property_keys=("v_p", "v_s1")),
        "spherical_summary": SimpleNamespace(property_keys=("v_p",)),
        "property_surface_3d": SimpleNamespace(property_keys=("v_s1",)),
        "acoustic_surface_3d": SimpleNamespace(property_keys=()),
    }
    contexts = {
        "polarization_overlay": SimpleNamespace(values=(False, True)),
        "surface_type": SimpleNamespace(values=("phase", "slowness")),
    }
    inventory = SimpleNamespace(
        representation_by_key=lambda key: representations[key],
        context_by_key=lambda key: contexts[key],
    )
    namespace = SimpleNamespace(
        PlotOptions=Options,
        SurfaceOptions=Options,
        build_plots=lambda result, options: calls.append(("maps", options)) or object(),
        build_summary=lambda result, options: calls.append(("summary", options)) or object(),
        build_surfaces=lambda result, options: calls.append(("surfaces", options)) or object(),
    )
    adapter = adapter_for("seismic")
    for family in representations:
        adapter.build_plots(namespace, object(), family, inventory)

    assert len(calls) == 4
    for _kind, options in calls:
        assert options.include_polarizations is True
        assert options.polarization_stride == 1
    surface_options = [options for kind, options in calls if kind == "surfaces"]
    assert all(options.geometry == "unit_sphere" for options in surface_options)


def test_seismic_builders_do_not_invent_polarizations_when_tracking_is_absent() -> None:
    captured = []

    class Options:
        def __init__(self, **values):
            self.__dict__.update(values)

    inventory = SimpleNamespace(
        representation_by_key=lambda key: SimpleNamespace(property_keys=("v_s1",)),
        context_by_key=lambda key: SimpleNamespace(values=(False,)),
    )
    namespace = SimpleNamespace(
        PlotOptions=Options,
        build_plots=lambda result, options: captured.append(options) or object(),
    )
    adapter_for("seismic").build_plots(namespace, object(), "spherical_map", inventory)
    assert captured[0].include_polarizations is False


def test_seismic_property_surface_forwards_all_selected_scalar_fields() -> None:
    captured: list[object] = []

    class Options:
        def __init__(self, **values):
            self.__dict__.update(values)

    inventory = SimpleNamespace(
        representation_by_key=lambda key: SimpleNamespace(
            property_keys=("phase_v_p", "shear_anisotropy")
        ),
        context_by_key=lambda key: SimpleNamespace(values=(False,)),
    )
    namespace = SimpleNamespace(
        SurfaceOptions=Options,
        build_surfaces=lambda result, options: captured.append(options) or object(),
    )
    selection = PlotBuildSelection(
        family_key="property_surface_3d",
        property_keys=("phase_v_p", "shear_anisotropy"),
        contexts=(("surface_geometry", "unit_sphere"),),
    )

    adapter_for("seismic").build_plots(
        namespace,
        object(),
        "property_surface_3d",
        inventory,
        selection,
    )

    assert len(captured) == 1
    assert captured[0].properties == ("phase_v_p", "shear_anisotropy")
