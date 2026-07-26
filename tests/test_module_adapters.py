from __future__ import annotations

from types import SimpleNamespace

from quantas_gui.explorer.adapters import adapter_for, registered_adapters


def test_all_scientific_result_adapters_are_registered() -> None:
    assert set(registered_adapters()) == {
        "elasticity", "seismic", "ha", "qha", "thermoelasticity", "eos"
    }


def test_elasticity_declares_expensive_3d_family_without_building_it() -> None:
    calls = 0

    def get_result(result):
        nonlocal calls
        calls += 1
        return SimpleNamespace(properties_2d={})

    namespace = SimpleNamespace(get_result=get_result)
    families = adapter_for("elasticity").plot_families(namespace, object())
    assert [(item.key, item.cost) for item in families] == [("surface-3d", "high")]
    assert calls == 1


def test_eos_remains_outside_generic_plot_families() -> None:
    assert adapter_for("eos").plot_families(object(), object()) == ()
