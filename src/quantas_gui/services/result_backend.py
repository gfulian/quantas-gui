"""Quantas public-lifecycle backend for native result inspection.

This module is the only Results Explorer layer that opens native Quantas
results. Module-specific presentation is delegated to adapters that consume
only public ``quantas.api`` namespaces, inventories, reports, and PlotSpecs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol

from quantas_gui.explorer.adapters import adapter_for
from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotFamilyDescriptor,
    PlotSelectionSchema,
    ScientificExportDescriptor,
    TableFamilyDescriptor,
)
from quantas_gui.models.results import (
    EventView,
    InventoryItem,
    ResultOverview,
    ResultSummary,
)
from quantas_gui.services.eos_inspection import (
    build_eos_tables,
    decode_eos_plot_family,
    eos_plot_families,
    eos_table_families,
    render_structural_tables,
)
from quantas_gui.services.serialization import inventory_item, to_json_value


class ResultBackendError(RuntimeError):
    """Base error raised while opening or rendering a native result."""


class ResultBackendUnavailable(ResultBackendError):
    """Raised when the required Quantas public API cannot be used."""


class InvalidNativeResult(ResultBackendError):
    """Raised when a file is not a supported native Quantas result."""


class ResultBackend(Protocol):
    """Public-result operations required by the Results Explorer."""

    def inspect(self, path: Path) -> ResultOverview:
        """Return a lightweight inspection snapshot."""

    def table_families(self, path: Path) -> tuple[TableFamilyDescriptor, ...]:
        """Return lazily generated report families."""

    def build_tables(self, path: Path, family_key: str | None = None) -> Sequence[Any]:
        """Return neutral report-table objects."""

    def plot_families(self, path: Path) -> tuple[PlotFamilyDescriptor, ...]:
        """Return lazily generated plot families."""

    def plot_selection_schema(self, path: Path, family_key: str) -> PlotSelectionSchema:
        """Return result-aware scientific selectors for one plot family."""

    def build_plots(
        self,
        path: Path,
        family_key: str | None = None,
        selection: PlotBuildSelection | None = None,
    ) -> Any:
        """Return a neutral plot collection."""

    def render_plain_report(self, path: Path, family_key: str | None = None) -> str:
        """Return deterministic plain-text report content."""

    def scientific_exports(self, path: Path) -> tuple[ScientificExportDescriptor, ...]:
        """Return public scientific export operations and GUI readiness."""

    def write_scientific_export(
        self,
        path: Path,
        operation_key: str,
        destination: Path,
    ) -> Path:
        """Run one configured public export operation."""

    def table_group(self, path: Path, title: str) -> str:
        """Return a module-aware group label for one report table."""

    def plot_group(self, path: Path, title: str, kind: str, family_key: str) -> str:
        """Return a module-aware group label for one plot."""

    def plot_description(self, path: Path, title: str, kind: str, family_key: str) -> str:
        """Return a module-aware plot description."""


@dataclass(frozen=True, slots=True)
class QuantasResultBackend:
    """Adapter that depends only on :mod:`quantas.api` public namespaces."""

    def inspect(self, path: Path) -> ResultOverview:
        """Inspect one native result through metadata-driven API dispatch."""
        descriptor = self._descriptor(path)
        if descriptor.name == "eos":
            return self._inspect_eos_archive(descriptor, path)
        return self._inspect_result_envelope(descriptor, self._open_result(path))

    def table_families(self, path: Path) -> tuple[TableFamilyDescriptor, ...]:
        """List report families without constructing their tables."""
        descriptor = self._descriptor(path)
        if descriptor.name == "eos":
            eos = self._namespace("eos")
            inventory = self._describe_eos(eos, path)
            return eos_table_families(inventory)
        result = self._open_result(path)
        namespace = descriptor.load()
        return adapter_for(descriptor.name).table_families(namespace, result)

    def build_tables(
        self,
        path: Path,
        family_key: str | None = None,
    ) -> Sequence[Any]:
        """Build one report family lazily for one native result."""
        descriptor = self._descriptor(path)
        if descriptor.name == "eos":
            eos = self._namespace("eos")
            inventory = self._describe_eos(eos, path)
            return build_eos_tables(eos, path, inventory, family_key)

        result = self._open_result(path)
        namespace = descriptor.load()
        adapter = adapter_for(descriptor.name)
        families = adapter.table_families(namespace, result)
        selected = family_key or _default_key(families)
        if selected is None:
            return ()
        try:
            return tuple(adapter.build_tables(namespace, result, selected))
        except Exception as exc:
            raise ResultBackendError(f"unable to build result tables: {exc}") from exc

    def plot_families(self, path: Path) -> tuple[PlotFamilyDescriptor, ...]:
        """List result-aware plot families without calculating figures."""
        descriptor = self._descriptor(path)
        if descriptor.name == "eos":
            eos = self._namespace("eos")
            inventory = self._describe_eos(eos, path)
            return eos_plot_families(inventory)

        result = self._open_result(path)
        namespace = descriptor.load()
        try:
            inventory = namespace.describe_plots(result)
            return adapter_for(descriptor.name).plot_families(
                namespace,
                result,
                inventory,
            )
        except Exception as exc:
            raise ResultBackendError(f"unable to inspect plot families: {exc}") from exc

    def plot_selection_schema(self, path: Path, family_key: str) -> PlotSelectionSchema:
        """Describe property and context selectors without building PlotSpecs."""
        descriptor = self._descriptor(path)
        if descriptor.name == "eos":
            eos = self._namespace("eos")
            inventory = self._describe_eos(eos, path)
            family = next(
                (item for item in eos_plot_families(inventory) if item.key == family_key),
                None,
            )
            if family is None:
                raise KeyError(f"unknown EOS plot family {family_key!r}")
            return PlotSelectionSchema(
                family_key=family.key,
                title=family.title,
                description=family.description,
                constraints=family.constraints,
                warnings=tuple(str(item) for item in inventory.warnings),
            )
        result = self._open_result(path)
        namespace = descriptor.load()
        inventory = namespace.describe_plots(result)
        return adapter_for(descriptor.name).plot_selection_schema(
            namespace, result, family_key, inventory
        )

    def build_plots(
        self,
        path: Path,
        family_key: str | None = None,
        selection: PlotBuildSelection | None = None,
    ) -> Any:
        """Build one selected PlotSpec family lazily for one native result."""
        descriptor = self._descriptor(path)
        if descriptor.name == "eos":
            eos = self._namespace("eos")
            inventory = self._describe_eos(eos, path)
            families = eos_plot_families(inventory)
            selected = family_key or _default_key(families)
            if selected is None:
                return _EmptyPlotCollection(warnings=list(inventory.warnings))
            if selected == "eos_select_record":
                return _EmptyPlotCollection(
                    warnings=[
                        *[str(item) for item in inventory.warnings],
                        "Select an explicit EOS record and representation to build a plot.",
                    ]
                )
            record_id, representation_key = decode_eos_plot_family(selected)
            try:
                return eos.build_plots(
                    path,
                    (representation_key,),
                    record_id=record_id,
                )
            except Exception as exc:
                raise ResultBackendError(f"unable to build EOS plots: {exc}") from exc

        result = self._open_result(path)
        namespace = descriptor.load()
        adapter = adapter_for(descriptor.name)
        try:
            inventory = namespace.describe_plots(result)
            families = adapter.plot_families(namespace, result, inventory)
            selected = (
                (selection.family_key if selection is not None else None)
                or family_key
                or _default_key(families)
            )
            if selected is None:
                return _EmptyPlotCollection(
                    warnings=["This result does not expose a compatible plot family."]
                )
            if selection is None:
                schema = adapter.plot_selection_schema(namespace, result, selected, inventory)
                selection = adapter.default_plot_selection(schema)
            return adapter.build_plots(namespace, result, selected, inventory, selection=selection)
        except Exception as exc:
            raise ResultBackendError(f"unable to build result plots: {exc}") from exc

    def scientific_exports(self, path: Path) -> tuple[ScientificExportDescriptor, ...]:
        """Discover public export operations without constructing export files."""
        descriptor = self._descriptor(path)
        registry = self._namespace("registry")
        operations = tuple(descriptor.list_operations(registry.Capability.EXPORT))
        namespace = descriptor.load()
        result = (
            self._describe_eos(namespace, path)
            if descriptor.name == "eos"
            else self._open_result(path)
        )
        return adapter_for(descriptor.name).scientific_exports(
            namespace,
            result,
            operations,
        )

    def write_scientific_export(
        self,
        path: Path,
        operation_key: str,
        destination: Path,
    ) -> Path:
        """Run one export through the public module API and return its path."""
        descriptor = self._descriptor(path)
        namespace = descriptor.load()
        exports = self.scientific_exports(path)
        selected = next((item for item in exports if item.key == operation_key), None)
        if selected is None:
            raise KeyError(f"unknown scientific export {operation_key!r}")
        if not selected.enabled:
            reason = selected.unavailable_reason or "additional scientific selections are required"
            raise ResultBackendError(reason)
        if descriptor.name == "eos":
            result = self._describe_eos(namespace, path)
        else:
            result = self._open_result(path)
        try:
            written = adapter_for(descriptor.name).write_scientific_export(
                namespace,
                result,
                operation_key,
                destination,
            )
        except Exception as exc:
            raise ResultBackendError(f"unable to write scientific export: {exc}") from exc
        return Path(written)

    def render_plain_report(
        self,
        path: Path,
        family_key: str | None = None,
    ) -> str:
        """Render one report family with deterministic plain text."""
        descriptor = self._descriptor(path)
        tables = self.build_tables(path, family_key=family_key)
        if descriptor.name == "eos":
            return render_structural_tables(tables)
        rendering = self._namespace("rendering")
        try:
            return str(rendering.render_tables(tables))
        except Exception as exc:
            raise ResultBackendError(f"unable to render plain-text report: {exc}") from exc

    def module_name(self, path: Path) -> str:
        """Return the stable module identifier stored in one native result."""
        return str(self._descriptor(path).name)

    def table_group(self, path: Path, title: str) -> str:
        """Return the module-aware group label for one table title."""
        return adapter_for(self.module_name(path)).table_group(title)

    def plot_group(self, path: Path, title: str, kind: str, family_key: str) -> str:
        """Return the module-aware group label for one plot."""
        return adapter_for(self.module_name(path)).plot_group(title, kind, family_key)

    def plot_description(
        self,
        path: Path,
        title: str,
        kind: str,
        family_key: str,
    ) -> str:
        """Return a module-aware description for one plot."""
        return adapter_for(self.module_name(path)).plot_description(
            title,
            kind,
            family_key,
        )

    def _descriptor(self, path: Path) -> Any:
        registry = self._namespace("registry")
        try:
            return registry.module_from_result(path)
        except Exception as exc:
            raise InvalidNativeResult(str(exc)) from exc

    def _open_result(self, path: Path) -> Any:
        registry = self._namespace("registry")
        try:
            return registry.open_result(path)
        except Exception as exc:
            raise InvalidNativeResult(str(exc)) from exc

    def _inspect_result_envelope(self, descriptor: Any, result: Any) -> ResultOverview:
        metadata = result.metadata
        input_data = result.input_data
        input_view: dict[str, Any] = {}
        if input_data is not None:
            input_view = {
                "source": to_json_value(input_data.source),
                "raw": None
                if input_data.raw is None
                else {"type": "text", "characters": len(input_data.raw)},
                "data": to_json_value(input_data.data),
            }

        events = tuple(self._event_view(event) for event in result.events)
        warnings = tuple(str(item) for item in result.warnings)
        capabilities = tuple(sorted(capability.value for capability in descriptor.capabilities))
        inventory = tuple(
            InventoryItem(**inventory_item(str(key), value))
            for key, value in result.results.items()
        )
        summary = ResultSummary(
            module=str(metadata.module),
            module_title=str(descriptor.title),
            method=str(metadata.method),
            program=str(metadata.program),
            quantas_version=str(metadata.version),
            schema_version=str(metadata.schema_version),
            created_at=to_json_value(metadata.created_at),
            created_by=None if metadata.created_by is None else str(metadata.created_by),
            capabilities=capabilities,
            warning_count=len(warnings),
            event_count=len(events),
            result_keys=tuple(str(key) for key in result.results),
            archive=False,
        )
        return ResultOverview(
            summary=summary,
            metadata={
                "program": summary.program,
                "module": summary.module,
                "method": summary.method,
                "version": summary.quantas_version,
                "schema_version": summary.schema_version,
                "created_at": summary.created_at,
                "created_by": summary.created_by,
            },
            input_data=input_view,
            options=to_json_value(result.options),
            inventory=inventory,
            warnings=warnings,
            events=events,
        )

    def _inspect_eos_archive(self, descriptor: Any, path: Path) -> ResultOverview:
        eos = self._namespace("eos")
        inventory = self._describe_eos(eos, path)
        capabilities = tuple(sorted(capability.value for capability in descriptor.capabilities))
        result_keys = tuple(item.key for item in inventory.slots)
        summary = ResultSummary(
            module="eos",
            module_title=str(descriptor.title),
            method="EOS archive",
            program="quantas",
            quantas_version=None,
            schema_version=str(inventory.schema_version),
            created_at=None,
            created_by=None,
            capabilities=capabilities,
            warning_count=len(inventory.warnings),
            event_count=int(inventory.event_count),
            result_keys=result_keys,
            archive=True,
        )
        compact_inventory: tuple[InventoryItem, ...] = (
            InventoryItem(
                key="datasets",
                value_type="EOSDatasetPlotDescriptor",
                shape=(len(inventory.datasets),),
                summary=f"{len(inventory.datasets)} embedded datasets",
            ),
            InventoryItem(
                key="slots",
                value_type="EOSSlotPlotDescriptor",
                shape=(len(inventory.slots),),
                summary=f"{len(inventory.slots)} result slots",
            ),
            InventoryItem(
                key="records",
                value_type="EOSRecordPlotDescriptor",
                shape=(len(inventory.records),),
                summary=f"{len(inventory.records)} immutable fit records",
            ),
        )
        if inventory.selected_plots is not None:
            compact_inventory += (
                InventoryItem(
                    key="selected_plots",
                    value_type="PlotInventory",
                    shape=(len(inventory.selected_plots.representations),),
                    summary=(
                        f"record #{inventory.selected_record_id}: "
                        f"{len(inventory.selected_plots.representations)} representations"
                    ),
                ),
            )
        return ResultOverview(
            summary=summary,
            metadata={
                "program": "quantas",
                "module": "eos",
                "method": "EOS archive",
                "schema_version": summary.schema_version,
                "selected_record_id": inventory.selected_record_id,
            },
            input_data={
                "datasets": [
                    {
                        "dataset_id": item.dataset_id,
                        "jobname": item.jobname,
                        "npoints": item.npoints,
                        "selected_npoints": item.selected_npoints,
                        "excluded_npoints": item.excluded_npoints,
                        "columns": list(item.columns),
                        "units": dict(item.units),
                    }
                    for item in inventory.datasets
                ]
            },
            options={
                "selected_record_id": inventory.selected_record_id,
                "selected_representations": []
                if inventory.selected_plots is None
                else [item.key for item in inventory.selected_plots.representations],
            },
            inventory=compact_inventory,
            warnings=tuple(str(item) for item in inventory.warnings),
            events=(),
        )

    @staticmethod
    def _describe_eos(eos: Any, path: Path) -> Any:
        try:
            return eos.describe_plots(path)
        except Exception as exc:
            raise InvalidNativeResult(str(exc)) from exc

    @staticmethod
    def _event_view(event: Any) -> EventView:
        timestamp = getattr(event, "timestamp", None)
        level_value = getattr(event, "level", getattr(event, "event_type", "info"))
        if isinstance(level_value, Enum):
            level_value = level_value.value
        return EventView(
            level=str(level_value),
            message=str(
                getattr(
                    event,
                    "message",
                    getattr(event, "note", None) or type(event).__name__,
                )
            ),
            timestamp=None if timestamp is None else str(to_json_value(timestamp)),
            progress=getattr(event, "progress", None),
            data=to_json_value(getattr(event, "data", getattr(event, "metadata", {}))),
        )

    @staticmethod
    def _namespace(name: str) -> Any:
        try:
            return import_module(f"quantas.api.{name}")
        except ImportError as exc:
            raise ResultBackendUnavailable(
                "Quantas is not installed or quantas.api is unavailable"
            ) from exc


@dataclass(slots=True)
class _EmptyPlotCollection:
    """Small structural plot collection used for archive-only messages."""

    plots: list[Any]
    warnings: list[str]

    def __init__(
        self,
        plots: list[Any] | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        self.plots = [] if plots is None else plots
        self.warnings = [] if warnings is None else warnings


def _default_key(families: Sequence[Any]) -> str | None:
    for family in families:
        if bool(getattr(family, "default", False)):
            return str(family.key)
    return str(families[0].key) if families else None
