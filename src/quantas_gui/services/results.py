"""Server-side orchestration for the HDF5 Results Explorer."""

from __future__ import annotations

from base64 import b64decode
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar
from uuid import uuid4

from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotFamilyDescriptor,
    PlotSelectionSchema,
    ScientificExportDescriptor,
    TableFamilyDescriptor,
)
from quantas_gui.models.results import ResultOverview, ResultReference
from quantas_gui.services.backend_info import BackendCompatibility
from quantas_gui.services.cache import ArtifactCache, LocalArtifactCache
from quantas_gui.services.result_backend import (
    ResultBackend,
    ResultBackendError,
    ResultBackendUnavailable,
)
from quantas_gui.services.workspaces import WorkspaceStore

ValueT = TypeVar("ValueT")


class ResultUploadError(ValueError):
    """Raised when an uploaded result violates the Explorer input policy."""


_ALLOWED_SUFFIXES = {".h5", ".hdf5", ".hdf"}


@dataclass(frozen=True, slots=True)
class ResultExplorerService:
    """Coordinate controlled storage, Quantas readers, and prepared artifacts.

    Browser state contains only opaque references. Every uncached HDF5 read is
    performed while the workspace store holds its cross-process lock. Closing a
    disposable result invalidates in-flight cache generations first, then waits
    for active readers before deleting the workspace.
    """

    workspace_store: WorkspaceStore
    backend: ResultBackend
    max_upload_bytes: int
    compatibility: BackendCompatibility
    cache: ArtifactCache = field(default_factory=LocalArtifactCache)

    def ingest_upload(
        self,
        *,
        filename: str,
        contents: str,
    ) -> tuple[ResultReference, ResultOverview]:
        """Validate, store, and inspect one browser upload atomically."""
        self._require_backend()
        display_name = _display_filename(filename)
        if not display_name:
            raise ResultUploadError("the uploaded file has no valid name")
        if Path(display_name).suffix.lower() not in _ALLOWED_SUFFIXES:
            raise ResultUploadError("select an HDF5 file with .h5, .hdf5, or .hdf suffix")

        payload = _decode_upload(contents)
        if not payload:
            raise ResultUploadError("the uploaded file is empty")
        if len(payload) > self.max_upload_bytes:
            limit_mib = self.max_upload_bytes / 1024.0**2
            raise ResultUploadError(f"the uploaded file exceeds the {limit_mib:.0f} MiB limit")

        workspace_id = self.workspace_store.create_workspace()
        result_id = uuid4().hex
        self.workspace_store.write_result_bytes(
            workspace_id=workspace_id,
            result_id=result_id,
            payload=payload,
        )
        reference = ResultReference(
            workspace_id=workspace_id,
            result_id=result_id,
            filename=display_name,
            size_bytes=len(payload),
        )
        try:
            overview = self.inspect(reference)
        except Exception:
            self.cache.invalidate_prefix(self._prefix(reference))
            self.workspace_store.delete_workspace(workspace_id)
            raise
        return reference, overview

    def register_result(
        self,
        *,
        workspace_id: str,
        result_id: str,
        filename: str,
        disposable_workspace: bool = False,
    ) -> tuple[ResultReference, ResultOverview]:
        """Register an existing controlled workflow result for exploration."""
        self._require_backend()
        display_name = _display_filename(filename)
        if not display_name or Path(display_name).suffix.lower() not in _ALLOWED_SUFFIXES:
            raise ResultUploadError("register an HDF5 result with .h5, .hdf5, or .hdf suffix")
        with self.workspace_store.result_access(
            workspace_id=workspace_id,
            result_id=result_id,
        ) as path:
            if not path.is_file():
                raise FileNotFoundError("the controlled workflow result does not exist")
            size_bytes = path.stat().st_size
        reference = ResultReference(
            workspace_id=workspace_id,
            result_id=result_id,
            filename=display_name,
            size_bytes=size_bytes,
            disposable_workspace=disposable_workspace,
        )
        return reference, self.inspect(reference)

    def open_reference(self, reference: ResultReference) -> ResultOverview:
        """Validate and inspect an existing opaque result reference."""
        with self.workspace_store.result_access(
            workspace_id=reference.workspace_id,
            result_id=reference.result_id,
        ) as path:
            if not path.is_file():
                raise FileNotFoundError("the referenced result is no longer available")
        return self.inspect(reference)

    def inspect(self, reference: ResultReference) -> ResultOverview:
        """Return a cached lightweight inspection snapshot."""
        self._require_backend()
        return self.cache.get_or_create(
            self._key(reference, "overview"),
            lambda: self._read(reference, self.backend.inspect),
        )

    def table_families(self, reference: ResultReference) -> tuple[TableFamilyDescriptor, ...]:
        """Return cached module-aware report-family descriptors."""
        self._require_backend()
        return self.cache.get_or_create(
            self._key(reference, "table-families"),
            lambda: tuple(self._read(reference, self.backend.table_families)),
        )

    def build_tables(
        self,
        reference: ResultReference,
        family_key: str | None = None,
    ) -> tuple[Any, ...]:
        """Build and cache one report family lazily."""
        self._require_backend()
        selected = family_key or _default_family(self.table_families(reference))
        return self.cache.get_or_create(
            self._key(reference, "tables", selected or "none"),
            lambda: tuple(
                self._read(
                    reference,
                    lambda path: self.backend.build_tables(path, selected),
                )
            ),
        )

    def plot_families(self, reference: ResultReference) -> tuple[PlotFamilyDescriptor, ...]:
        """Return cached module-aware plot-family descriptors."""
        self._require_backend()
        return self.cache.get_or_create(
            self._key(reference, "plot-families"),
            lambda: tuple(self._read(reference, self.backend.plot_families)),
        )

    def plot_selection_schema(
        self,
        reference: ResultReference,
        family_key: str,
    ) -> PlotSelectionSchema:
        """Return cached scientific selectors for one result-aware family."""
        self._require_backend()
        return self.cache.get_or_create(
            self._key(reference, "plot-selection-schema", family_key),
            lambda: self._read(
                reference,
                lambda path: self.backend.plot_selection_schema(path, family_key),
            ),
        )

    def build_plots(
        self,
        reference: ResultReference,
        family_key: str | None = None,
        selection: PlotBuildSelection | None = None,
    ) -> Any:
        """Build and cache one PlotCollection for one scientific selection."""
        self._require_backend()
        selected = (
            (selection.family_key if selection is not None else None)
            or family_key
            or _default_family(self.plot_families(reference))
        )
        token = selection.cache_token() if selection is not None else "default"

        def build(path: Path) -> Any:
            if selection is None:
                return self.backend.build_plots(path, selected)
            return self.backend.build_plots(path, selected, selection=selection)

        return self.cache.get_or_create(
            self._key(reference, "plots", selected or "none", token),
            lambda: self._read(reference, build),
        )

    def scientific_exports(
        self,
        reference: ResultReference,
    ) -> tuple[ScientificExportDescriptor, ...]:
        """Return cached public export descriptors for one result."""
        self._require_backend()
        return self.cache.get_or_create(
            self._key(reference, "scientific-exports"),
            lambda: tuple(self._read(reference, self.backend.scientific_exports)),
        )

    def build_scientific_export(
        self,
        reference: ResultReference,
        operation_key: str,
    ) -> Path:
        """Build and atomically publish one public scientific export."""
        self._require_backend()
        descriptor = next(
            (item for item in self.scientific_exports(reference) if item.key == operation_key),
            None,
        )
        if descriptor is None:
            raise KeyError(f"unknown scientific export {operation_key!r}")
        if not descriptor.enabled:
            raise ResultBackendError(
                descriptor.unavailable_reason or "additional scientific selections are required"
            )
        stem = _safe_stem(reference.filename)
        destination = self.workspace_store.export_path(
            workspace_id=reference.workspace_id,
            result_id=reference.result_id,
            filename=f"{stem}-{operation_key}{descriptor.suffix}",
        )

        def build() -> Path:
            with self.workspace_store.atomic_output(destination) as temporary:
                source = self.path(reference)
                if not source.is_file():
                    raise FileNotFoundError("the referenced result is no longer available")
                self.backend.write_scientific_export(
                    source,
                    operation_key,
                    temporary,
                )
            return destination

        return self.cache.get_or_create(
            self._key(reference, "scientific-export", operation_key),
            build,
        )

    def render_plain_report(
        self,
        reference: ResultReference,
        family_key: str | None = None,
    ) -> str:
        """Return a cached deterministic plain-text report."""
        self._require_backend()
        selected = family_key or _default_family(self.table_families(reference))
        return self.cache.get_or_create(
            self._key(reference, "plain-report", selected or "none"),
            lambda: self._read(
                reference,
                lambda path: self.backend.render_plain_report(path, selected),
            ),
        )

    def table_group(self, reference: ResultReference, title: str) -> str:
        """Return the module-aware group label for one table."""
        self._require_backend()
        return self._read(reference, lambda path: self.backend.table_group(path, title))

    def plot_group(
        self,
        reference: ResultReference,
        title: str,
        kind: str,
        family_key: str,
    ) -> str:
        """Return the module-aware group label for one plot."""
        self._require_backend()
        return self._read(
            reference,
            lambda path: self.backend.plot_group(path, title, kind, family_key),
        )

    def plot_description(
        self,
        reference: ResultReference,
        title: str,
        kind: str,
        family_key: str,
    ) -> str:
        """Return a module-aware description for one plot."""
        self._require_backend()
        return self._read(
            reference,
            lambda path: self.backend.plot_description(path, title, kind, family_key),
        )

    def path(self, reference: ResultReference) -> Path:
        """Resolve an opaque reference; callers must hold workspace access."""
        return self.workspace_store.result_path(
            workspace_id=reference.workspace_id,
            result_id=reference.result_id,
        )

    def close(self, reference: ResultReference) -> None:
        """Close a result and delete only Explorer-owned disposable workspaces."""
        self.cache.invalidate_prefix(self._prefix(reference))
        if reference.disposable_workspace:
            self.workspace_store.delete_workspace(reference.workspace_id)

    def _read(self, reference: ResultReference, operation: Callable[[Path], ValueT]) -> ValueT:
        with self.workspace_store.result_access(
            workspace_id=reference.workspace_id,
            result_id=reference.result_id,
        ) as path:
            if not path.is_file():
                raise FileNotFoundError("the referenced result is no longer available")
            return operation(path)

    def _require_backend(self) -> None:
        if not self.compatibility.ready:
            raise ResultBackendUnavailable(self.compatibility.diagnostic_message())

    @staticmethod
    def _prefix(reference: ResultReference) -> tuple[str, str]:
        return reference.workspace_id, reference.result_id

    def _key(self, reference: ResultReference, *parts: str) -> tuple[str, ...]:
        return (*self._prefix(reference), *parts)


def _default_family(families: tuple[Any, ...]) -> str | None:
    for family in families:
        if bool(getattr(family, "default", False)):
            return str(family.key)
    return str(families[0].key) if families else None


def _decode_upload(contents: str) -> bytes:
    """Decode a Dash data URL and reject malformed payloads."""
    if not isinstance(contents, str) or "," not in contents:
        raise ResultUploadError("the browser upload payload is malformed")
    header, encoded = contents.split(",", 1)
    if ";base64" not in header.lower():
        raise ResultUploadError("the browser upload payload is not base64 encoded")
    try:
        return b64decode(encoded, validate=True)
    except Exception as exc:
        raise ResultUploadError("the browser upload payload could not be decoded") from exc


def _display_filename(filename: str) -> str:
    """Return a bounded display name for POSIX or Windows browser paths."""
    candidate = Path(str(filename).replace("\\", "/")).name.strip()
    candidate = "".join(
        character for character in candidate if character.isprintable() and character != "\x00"
    )
    if len(candidate) <= 240:
        return candidate
    suffix = Path(candidate).suffix
    stem_limit = max(1, 240 - len(suffix))
    return f"{candidate[:stem_limit]}{suffix}"


def _safe_stem(filename: str) -> str:
    """Return a bounded safe stem for a derived download filename."""
    stem = Path(str(filename).replace("\\", "/")).stem.lower()
    cleaned = "".join(character if character.isalnum() else "-" for character in stem)
    return "-".join(part for part in cleaned.split("-") if part) or "quantas-result"
