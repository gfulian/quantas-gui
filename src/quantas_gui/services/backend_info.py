"""Runtime validation of the Quantas public lifecycle API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from types import ModuleType

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

REQUIRED_QUANTAS = ">=2.0.0b7,<2.1"
_EXPECTED_MODULES = (
    "elasticity",
    "seismic",
    "ha",
    "qha",
    "eos",
    "thermoelasticity",
)
_PLOT_TYPES = (
    "LinePlotSpec",
    "ContourPlotSpec",
    "PolarPlotSpec",
    "SurfacePlotSpec",
    "SphericalMapSpec",
    "SphericalSummarySpec",
    "PanelPlotSpec",
    "PlotCollection",
    "PlotInventory",
)
_REQUIRED_MODULE_OPERATIONS: dict[str, tuple[str, ...]] = {
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

_WORKFLOW_MODULE_OPERATIONS: dict[str, tuple[str, ...]] = {
    module: ("read_input", "normalize_input", "run", "write_result")
    for module in ("elasticity", "seismic", "ha", "qha", "thermoelasticity")
}


@dataclass(frozen=True, slots=True)
class BackendCompatibility:
    """Immutable compatibility result for the required Quantas backend."""

    available: bool
    compatible: bool
    version: str | None
    required_version: str
    missing_capabilities: tuple[str, ...]
    detail: str | None
    workflow_missing: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def ready(self) -> bool:
        """Return whether scientific GUI functions may be enabled."""
        return self.available and self.compatible and not self.missing_capabilities

    def workflow_missing_for(self, module: str) -> tuple[str, ...]:
        """Return missing public lifecycle operations for one workflow module."""
        if module not in _WORKFLOW_MODULE_OPERATIONS:
            return ("unknown workflow module",)
        return dict(self.workflow_missing).get(module, ())

    def workflow_ready(self, module: str) -> bool:
        """Return whether one executable workflow has a complete public contract."""
        return self.ready and not self.workflow_missing_for(module)

    @property
    def status_label(self) -> str:
        """Return a concise user-facing backend state."""
        if self.ready:
            return f"Quantas {self.version} ready"
        if not self.available:
            return "Quantas unavailable"
        return f"Quantas {self.version or 'unknown'} incompatible"

    @property
    def recovery_action(self) -> str:
        """Return the operation required to restore scientific functions."""
        return (
            "Install or reinstall a compatible backend with "
            f"`python -m pip install 'quantas{self.required_version}'`."
        )

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return asdict(self)

    def diagnostic_message(self) -> str:
        """Return a complete accessible diagnostic message."""
        if self.ready:
            return f"Quantas {self.version} satisfies {self.required_version}."
        pieces = [
            f"Required Quantas version: {self.required_version}.",
            f"Detected version: {self.version or 'not available'}.",
        ]
        if self.missing_capabilities:
            pieces.append(
                "Missing public capabilities: " + ", ".join(self.missing_capabilities) + "."
            )
        if self.detail:
            pieces.append(self.detail.rstrip(".") + ".")
        pieces.append(self.recovery_action)
        return " ".join(pieces)


# Compatibility alias retained for code written against the foundation status object.
BackendInfo = BackendCompatibility


def detect_quantas_backend(
    *,
    version_resolver: Callable[[str], str] = version,
    importer: Callable[[str], ModuleType] = import_module,
) -> BackendCompatibility:
    """Validate the installed backend version and public lifecycle contract.

    The probe never imports implementation namespaces and never compensates for
    a missing public capability through a private Quantas module.
    """
    try:
        backend_version = version_resolver("quantas")
    except PackageNotFoundError as exc:
        return BackendCompatibility(
            available=False,
            compatible=False,
            version=None,
            required_version=REQUIRED_QUANTAS,
            missing_capabilities=("quantas.api",),
            detail=f"The Quantas distribution is not installed ({exc.__class__.__name__})",
        )
    except Exception as exc:
        return BackendCompatibility(
            available=False,
            compatible=False,
            version=None,
            required_version=REQUIRED_QUANTAS,
            missing_capabilities=("quantas.api",),
            detail=f"Unable to inspect the Quantas distribution: {exc}",
        )

    try:
        parsed_version = Version(backend_version)
        version_compatible = parsed_version in SpecifierSet(REQUIRED_QUANTAS)
    except InvalidVersion as exc:
        return BackendCompatibility(
            available=True,
            compatible=False,
            version=backend_version,
            required_version=REQUIRED_QUANTAS,
            missing_capabilities=(),
            detail=f"The installed Quantas version is not PEP 440 compatible: {exc}",
        )

    try:
        api = importer("quantas.api")
    except Exception as exc:
        return BackendCompatibility(
            available=True,
            compatible=False,
            version=backend_version,
            required_version=REQUIRED_QUANTAS,
            missing_capabilities=("quantas.api",),
            detail=f"Importing quantas.api failed: {exc}",
        )

    missing = _missing_public_capabilities(api, importer=importer)
    workflow_missing = _missing_workflow_capabilities(importer=importer)
    details: list[str] = []
    if not version_compatible:
        details.append(f"Version {backend_version} does not satisfy {REQUIRED_QUANTAS}")
    if missing:
        details.append("The installed public lifecycle API is incomplete")
    return BackendCompatibility(
        available=True,
        compatible=version_compatible and not missing,
        version=backend_version,
        required_version=REQUIRED_QUANTAS,
        missing_capabilities=missing,
        detail="; ".join(details) or "Public lifecycle API validated",
        workflow_missing=workflow_missing,
    )


def _missing_public_capabilities(
    api: ModuleType,
    *,
    importer: Callable[[str], ModuleType],
) -> tuple[str, ...]:
    missing: list[str] = []
    for namespace_name in ("registry", "plotting", *_EXPECTED_MODULES):
        if not hasattr(api, namespace_name):
            missing.append(f"quantas.api.{namespace_name}")

    try:
        registry = importer("quantas.api.registry")
    except Exception as exc:
        missing.append(f"quantas.api.registry ({exc.__class__.__name__})")
        return tuple(sorted(set(missing)))

    for name in (
        "Capability",
        "ModuleDescriptor",
        "list_modules",
        "get",
        "module_from_result",
        "open_result",
    ):
        if not hasattr(registry, name):
            missing.append(f"registry.{name}")

    descriptor_names: set[str] = set()
    try:
        descriptors = tuple(registry.list_modules())
        descriptor_names = {str(item.name) for item in descriptors}
    except Exception as exc:
        missing.append(f"registry.list_modules ({exc.__class__.__name__})")
        descriptors = ()
    for module_name in _EXPECTED_MODULES:
        if module_name not in descriptor_names:
            missing.append(f"registry.module:{module_name}")

    capability_type = getattr(registry, "Capability", None)
    for descriptor in descriptors:
        module_name = str(getattr(descriptor, "name", ""))
        if module_name not in _EXPECTED_MODULES:
            continue
        if capability_type is not None:
            try:
                if not descriptor.has(capability_type.PLOT_INVENTORY):
                    missing.append(f"{module_name}.PLOT_INVENTORY")
            except Exception:
                missing.append(f"{module_name}.PLOT_INVENTORY")
        try:
            namespace = descriptor.load()
        except Exception as exc:
            missing.append(f"{module_name}.load ({exc.__class__.__name__})")
            continue
        for operation_name in _REQUIRED_MODULE_OPERATIONS[module_name]:
            if not callable(getattr(namespace, operation_name, None)):
                missing.append(f"{module_name}.{operation_name}")
        if not callable(getattr(namespace, "describe_plots", None)):
            missing.append(f"{module_name}.PLOT_INVENTORY")
        for method_name in ("list_operations", "operations_for", "named_operation"):
            if not callable(getattr(descriptor, method_name, None)):
                missing.append(f"registry.{module_name}.{method_name}")

    try:
        plotting = importer("quantas.api.plotting")
    except Exception as exc:
        missing.append(f"quantas.api.plotting ({exc.__class__.__name__})")
    else:
        for name in _PLOT_TYPES:
            if not isinstance(getattr(plotting, name, None), type):
                missing.append(f"plotting.{name}")

    return tuple(sorted(set(missing)))


def _missing_workflow_capabilities(
    *,
    importer: Callable[[str], ModuleType],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    missing_by_module: list[tuple[str, tuple[str, ...]]] = []
    for module_name, operations in _WORKFLOW_MODULE_OPERATIONS.items():
        try:
            namespace = importer(f"quantas.api.{module_name}")
        except Exception as exc:
            missing_by_module.append((module_name, (f"load ({exc.__class__.__name__})",)))
            continue
        missing = tuple(
            operation
            for operation in operations
            if not callable(getattr(namespace, operation, None))
        )
        if missing:
            missing_by_module.append((module_name, missing))
    return tuple(missing_by_module)


__all__ = [
    "BackendCompatibility",
    "BackendInfo",
    "REQUIRED_QUANTAS",
    "detect_quantas_backend",
]
