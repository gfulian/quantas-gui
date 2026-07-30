from __future__ import annotations

from importlib import import_module
from importlib.metadata import PackageNotFoundError
from types import ModuleType
from typing import Any

import pytest

from quantas_gui.services.backend_info import (
    REQUIRED_QUANTAS,
    BackendCompatibility,
    detect_quantas_backend,
)

_REQUIRED_OPERATIONS = {
    "elasticity": (
        "read_result",
        "build_report",
        "describe_plots",
        "build_plots",
        "create_input",
        "write_table",
    ),
    "seismic": (
        "read_result",
        "build_report",
        "describe_plots",
        "build_plots",
        "write_csv",
    ),
    "ha": (
        "read_result",
        "build_report",
        "describe_plots",
        "build_plots",
        "create_input",
        "write_table",
    ),
    "qha": (
        "read_result",
        "build_report",
        "describe_plots",
        "build_plots",
        "create_input",
        "write_table",
    ),
    "thermoelasticity": (
        "read_result",
        "build_report",
        "describe_plots",
        "build_plots",
        "create_input",
        "write_grid_table",
        "write_profile_table",
        "write_state_input",
    ),
    "eos": (
        "open_archive",
        "describe_plots",
        "build_plots",
        "write_diagnostic_csv",
        "write_calculation_csv",
        "write_spec_template",
    ),
}


class FakeDescriptor:
    def __init__(self, name: str, namespace: ModuleType) -> None:
        self.name = name
        self._namespace = namespace

    def load(self) -> ModuleType:
        return self._namespace

    def has(self, capability: Any) -> bool:
        del capability
        return True

    def list_operations(self, *_: Any) -> tuple[Any, ...]:
        return ()

    def operations_for(self, *_: Any) -> tuple[Any, ...]:
        return ()

    def named_operation(self, *_: Any) -> Any:
        raise KeyError


def _contract_modules() -> tuple[ModuleType, dict[str, ModuleType]]:
    api = ModuleType("quantas.api")
    modules: dict[str, ModuleType] = {"quantas.api": api}
    descriptors: list[FakeDescriptor] = []

    for module_name, operations in _REQUIRED_OPERATIONS.items():
        namespace = ModuleType(f"quantas.api.{module_name}")
        workflow_operations = (
            ("read_input", "normalize_input", "run", "write_result") if module_name != "eos" else ()
        )
        for operation in (*operations, *workflow_operations):
            setattr(namespace, operation, lambda *args, **kwargs: None)
        setattr(api, module_name, namespace)
        modules[namespace.__name__] = namespace
        descriptors.append(FakeDescriptor(module_name, namespace))

    registry = ModuleType("quantas.api.registry")
    registry.Capability = type("Capability", (), {"PLOT_INVENTORY": "plot_inventory"})
    registry.ModuleDescriptor = FakeDescriptor
    registry.list_modules = lambda: tuple(descriptors)
    registry.get = lambda name: next(item for item in descriptors if item.name == name)
    registry.module_from_result = lambda path: descriptors[0]
    registry.open_result = lambda path: object()
    api.registry = registry
    modules[registry.__name__] = registry

    plotting = ModuleType("quantas.api.plotting")
    for name in (
        "LinePlotSpec",
        "ContourPlotSpec",
        "PolarPlotSpec",
        "SurfacePlotSpec",
        "SphericalMapSpec",
        "SphericalSummarySpec",
        "PanelPlotSpec",
        "PlotCollection",
        "PlotInventory",
    ):
        setattr(plotting, name, type(name, (), {}))
    api.plotting = plotting
    modules[plotting.__name__] = plotting
    return api, modules


def _importer(modules: dict[str, ModuleType]):
    def import_one(name: str) -> ModuleType:
        return modules[name]

    return import_one


def test_backend_contract_accepts_supported_version() -> None:
    _, modules = _contract_modules()
    info = detect_quantas_backend(
        version_resolver=lambda _: "2.0.0b7",
        importer=_importer(modules),
    )
    assert info.ready
    assert info.compatible
    assert info.version == "2.0.0b7"
    assert info.required_version == REQUIRED_QUANTAS
    assert not info.missing_capabilities
    assert info.workflow_ready("elasticity")


def test_backend_absence_is_non_fatal_and_actionable() -> None:
    def missing(_: str) -> str:
        raise PackageNotFoundError("quantas")

    info = detect_quantas_backend(version_resolver=missing)
    assert not info.available
    assert not info.ready
    assert "quantas.api" in info.missing_capabilities
    assert REQUIRED_QUANTAS in info.diagnostic_message()
    assert "pip install" in info.recovery_action


@pytest.mark.parametrize("backend_version", ["2.0.0b6", "2.1.0"])
def test_backend_rejects_versions_outside_public_baseline(backend_version: str) -> None:
    _, modules = _contract_modules()
    info = detect_quantas_backend(
        version_resolver=lambda _: backend_version,
        importer=_importer(modules),
    )
    assert info.available
    assert not info.compatible
    assert not info.ready
    assert "does not satisfy" in (info.detail or "")


def test_backend_reports_missing_public_capability() -> None:
    _, modules = _contract_modules()
    delattr(modules["quantas.api.qha"], "describe_plots")
    info = detect_quantas_backend(
        version_resolver=lambda _: "2.0.0b7",
        importer=_importer(modules),
    )
    assert not info.ready
    assert "qha.describe_plots" in info.missing_capabilities
    assert "qha.PLOT_INVENTORY" in info.missing_capabilities


def test_real_quantas_b7_public_lifecycle_contract_is_accepted() -> None:
    info = detect_quantas_backend(
        version_resolver=lambda _: "2.0.0b7",
        importer=import_module,
    )
    assert info.ready, info.diagnostic_message()


def test_missing_workflow_operation_does_not_disable_result_explorer() -> None:
    _, modules = _contract_modules()
    delattr(modules["quantas.api.elasticity"], "run")
    info = detect_quantas_backend(
        version_resolver=lambda _: "2.0.0b7",
        importer=_importer(modules),
    )
    assert info.ready
    assert not info.workflow_ready("elasticity")
    assert info.workflow_missing_for("elasticity") == ("run",)


def test_unknown_workflow_module_is_not_reported_ready() -> None:
    compatibility = BackendCompatibility(
        available=True,
        compatible=True,
        version="2.0.0b7",
        required_version=REQUIRED_QUANTAS,
        missing_capabilities=(),
        detail="ready",
    )
    assert compatibility.workflow_ready("typo") is False
    assert compatibility.workflow_missing_for("typo") == ("unknown workflow module",)
