"""Optional Quantas backend adapter for native result inspection.

This module is the only Results Explorer layer that opens native Quantas
results.  Module-specific presentation is delegated to adapters that use only
public ``quantas.api`` namespaces.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol

from quantas_gui.explorer.adapters import adapter_for
from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor
from quantas_gui.models.results import (
    EventView,
    InventoryItem,
    ResultOverview,
    ResultSummary,
    TableData,
)
from quantas_gui.services.serialization import inventory_item, to_json_value


class ResultBackendError(RuntimeError):
    """Base error raised while opening or rendering a native result."""


class ResultBackendUnavailable(ResultBackendError):
    """Raised when the optional Quantas public API cannot be imported."""


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

    def build_plots(self, path: Path, family_key: str | None = None) -> Any:
        """Return a neutral plot collection."""

    def render_plain_report(self, path: Path, family_key: str | None = None) -> str:
        """Return deterministic plain-text report content."""

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
        descriptor, opened = self._open(path)
        if descriptor.name == "eos":
            return self._inspect_eos_archive(descriptor, opened)
        return self._inspect_result_envelope(descriptor, opened)

    def table_families(self, path: Path) -> tuple[TableFamilyDescriptor, ...]:
        """List report families without constructing their tables."""
        descriptor, opened = self._open(path)
        if descriptor.name == "eos":
            try:
                return (
                    TableFamilyDescriptor(
                        key="summary",
                        title="Archive summary",
                        description="Structural EOS archive metadata and slot inventory.",
                        default=True,
                    ),
                )
            finally:
                opened.close()
        namespace = descriptor.load()
        return adapter_for(descriptor.name).table_families(namespace, opened)

    def build_tables(
        self,
        path: Path,
        family_key: str | None = None,
    ) -> Sequence[Any]:
        """Build one report family lazily for one native result."""
        descriptor, opened = self._open(path)
        if descriptor.name == "eos":
            try:
                if family_key not in {None, "summary"}:
                    raise KeyError(f"unknown EOS report family {family_key!r}")
                summary = opened.summary()
                rows = [[key, to_json_value(value)] for key, value in summary.items()]
                return (
                    TableData(
                        title="EOS archive summary",
                        columns=["Property", "Value"],
                        rows=rows,
                    ),
                )
            finally:
                opened.close()

        namespace = descriptor.load()
        adapter = adapter_for(descriptor.name)
        families = adapter.table_families(namespace, opened)
        selected = family_key or _default_key(families)
        if selected is None:
            return ()
        try:
            return tuple(adapter.build_tables(namespace, opened, selected))
        except Exception as exc:
            raise ResultBackendError(f"unable to build result tables: {exc}") from exc

    def plot_families(self, path: Path) -> tuple[PlotFamilyDescriptor, ...]:
        """List module-aware plot families without calculating figures."""
        descriptor, opened = self._open(path)
        if descriptor.name == "eos":
            try:
                return ()
            finally:
                opened.close()
        namespace = descriptor.load()
        try:
            return adapter_for(descriptor.name).plot_families(namespace, opened)
        except Exception as exc:
            raise ResultBackendError(f"unable to inspect plot families: {exc}") from exc

    def build_plots(self, path: Path, family_key: str | None = None) -> Any:
        """Build one selected plot family lazily for one native result."""
        descriptor, opened = self._open(path)
        if descriptor.name == "eos":
            try:
                return _EmptyPlotCollection(
                    warnings=[
                        "EOS archives require selection of an accepted fit record before "
                        "plot specifications can be built."
                    ]
                )
            finally:
                opened.close()

        namespace = descriptor.load()
        adapter = adapter_for(descriptor.name)
        families = adapter.plot_families(namespace, opened)
        selected = family_key or _default_key(families)
        if selected is None:
            return _EmptyPlotCollection(
                warnings=["This result does not expose a compatible plot family."]
            )
        try:
            return adapter.build_plots(namespace, opened, selected)
        except Exception as exc:
            raise ResultBackendError(f"unable to build result plots: {exc}") from exc

    def render_plain_report(
        self,
        path: Path,
        family_key: str | None = None,
    ) -> str:
        """Render one report family with deterministic plain text."""
        registry = self._namespace("registry")
        descriptor = registry.module_from_result(path)
        tables = self.build_tables(path, family_key=family_key)
        if descriptor.name == "eos":
            return _render_structural_tables(tables)
        rendering = self._namespace("rendering")
        try:
            return str(rendering.render_tables(tables))
        except Exception as exc:
            raise ResultBackendError(f"unable to render plain-text report: {exc}") from exc

    def module_name(self, path: Path) -> str:
        """Return the stable module identifier stored in one native result."""
        registry = self._namespace("registry")
        try:
            return str(registry.module_from_result(path).name)
        except Exception as exc:
            raise InvalidNativeResult(str(exc)) from exc

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

    def _open(self, path: Path) -> tuple[Any, Any]:
        registry = self._namespace("registry")
        try:
            descriptor = registry.module_from_result(path)
            opened = registry.open_result(path)
        except Exception as exc:
            raise InvalidNativeResult(str(exc)) from exc
        return descriptor, opened

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

    def _inspect_eos_archive(self, descriptor: Any, archive: Any) -> ResultOverview:
        try:
            summary_map = dict(archive.summary())
            events = tuple(self._event_view(event) for event in archive.events())
            capabilities = tuple(sorted(capability.value for capability in descriptor.capabilities))
            result_keys = tuple(str(key) for key in summary_map.get("slots", {}))
            summary = ResultSummary(
                module="eos",
                module_title=str(descriptor.title),
                method="EOS archive",
                program="quantas",
                quantas_version=None,
                schema_version=str(summary_map.get("schema_version", "unknown")),
                created_at=None,
                created_by=None,
                capabilities=capabilities,
                warning_count=0,
                event_count=len(events),
                result_keys=result_keys,
                archive=True,
            )
            inventory = tuple(
                InventoryItem(**inventory_item(str(key), value))
                for key, value in summary_map.items()
                if key != "path"
            )
            return ResultOverview(
                summary=summary,
                metadata={
                    "program": "quantas",
                    "module": "eos",
                    "method": "EOS archive",
                    "schema_version": summary.schema_version,
                },
                input_data={"datasets": to_json_value(summary_map.get("datasets", []))},
                options={},
                inventory=inventory,
                warnings=(),
                events=events,
            )
        finally:
            archive.close()

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


def _render_structural_tables(tables: Sequence[Any]) -> str:
    """Render GUI-owned structural tables for archive-only workflows."""
    blocks: list[str] = []
    for table in tables:
        columns = [str(item) for item in table.columns]
        rows = [["" if value is None else str(value) for value in row] for row in table.rows]
        widths = [len(column) for column in columns]
        for row in rows:
            for index, value in enumerate(row[: len(widths)]):
                widths[index] = max(widths[index], len(value))
        heading = " ".join(value.ljust(widths[index]) for index, value in enumerate(columns))
        lines = [str(table.title), heading]
        lines.append(" ".join("-" * width for width in widths))
        for row in rows:
            padded = row + [""] * (len(widths) - len(row))
            lines.append(
                " ".join(
                    value.ljust(widths[index]) for index, value in enumerate(padded[: len(widths)])
                )
            )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
