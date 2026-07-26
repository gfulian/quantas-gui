"""Server-side orchestration for the HDF5 Results Explorer."""

from __future__ import annotations

from base64 import b64decode
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from quantas_gui.explorer.adapters import adapter_for
from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor
from quantas_gui.models.results import ResultOverview, ResultReference
from quantas_gui.services.cache import ArtifactCache, LocalArtifactCache
from quantas_gui.services.result_backend import ResultBackend
from quantas_gui.services.workspaces import LocalWorkspaceStore


class ResultUploadError(ValueError):
    """Raised when an uploaded result violates the Explorer input policy."""


_ALLOWED_SUFFIXES = {".h5", ".hdf5", ".hdf"}


@dataclass(frozen=True, slots=True)
class ResultExplorerService:
    """Coordinate controlled storage, Quantas readers, and prepared artifacts.

    The cache is deliberately server-side. Browser state contains only opaque
    result references and lightweight inventories, so this interface can later
    be backed by Redis or another shared cache without changing Dash pages.
    """

    workspace_store: LocalWorkspaceStore
    backend: ResultBackend
    max_upload_bytes: int
    cache: ArtifactCache = field(default_factory=LocalArtifactCache)

    def ingest_upload(
        self,
        *,
        filename: str,
        contents: str,
    ) -> tuple[ResultReference, ResultOverview]:
        """Validate, store, and inspect one browser upload atomically."""
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
        path = self.workspace_store.write_result_bytes(
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

    def inspect(self, reference: ResultReference) -> ResultOverview:
        """Return a cached lightweight inspection snapshot."""
        return self.cache.get_or_create(
            self._key(reference, "overview"),
            lambda: self.backend.inspect(self.path(reference)),
        )

    def table_families(self, reference: ResultReference) -> tuple[TableFamilyDescriptor, ...]:
        """Return cached module-aware report-family descriptors."""
        return self.cache.get_or_create(
            self._key(reference, "table-families"),
            lambda: tuple(self.backend.table_families(self.path(reference))),
        )

    def build_tables(
        self,
        reference: ResultReference,
        family_key: str | None = None,
    ) -> tuple[Any, ...]:
        """Build and cache one report family lazily."""
        selected = family_key or _default_family(self.table_families(reference))
        return self.cache.get_or_create(
            self._key(reference, "tables", selected or "none"),
            lambda: tuple(self.backend.build_tables(self.path(reference), selected)),
        )

    def plot_families(self, reference: ResultReference) -> tuple[PlotFamilyDescriptor, ...]:
        """Return cached module-aware plot-family descriptors."""
        return self.cache.get_or_create(
            self._key(reference, "plot-families"),
            lambda: tuple(self.backend.plot_families(self.path(reference))),
        )

    def build_plots(self, reference: ResultReference, family_key: str | None = None) -> Any:
        """Build and cache one PlotCollection family lazily."""
        selected = family_key or _default_family(self.plot_families(reference))
        return self.cache.get_or_create(
            self._key(reference, "plots", selected or "none"),
            lambda: self.backend.build_plots(self.path(reference), selected),
        )

    def render_plain_report(
        self,
        reference: ResultReference,
        family_key: str | None = None,
    ) -> str:
        """Return a cached deterministic plain-text report."""
        selected = family_key or _default_family(self.table_families(reference))
        return self.cache.get_or_create(
            self._key(reference, "plain-report", selected or "none"),
            lambda: self.backend.render_plain_report(self.path(reference), selected),
        )

    def table_group(self, reference: ResultReference, title: str) -> str:
        """Return the module-aware group label for one table."""
        return adapter_for(self.inspect(reference).summary.module).table_group(title)

    def plot_group(
        self,
        reference: ResultReference,
        title: str,
        kind: str,
        family_key: str,
    ) -> str:
        """Return the module-aware group label for one plot."""
        return adapter_for(self.inspect(reference).summary.module).plot_group(
            title, kind, family_key
        )

    def plot_description(
        self,
        reference: ResultReference,
        title: str,
        kind: str,
        family_key: str,
    ) -> str:
        """Return a module-aware description for one plot."""
        return adapter_for(self.inspect(reference).summary.module).plot_description(
            title, kind, family_key
        )

    def path(self, reference: ResultReference) -> Path:
        """Resolve one opaque result reference to its controlled path."""
        return self.workspace_store.result_path(
            workspace_id=reference.workspace_id,
            result_id=reference.result_id,
        )

    def close(self, reference: ResultReference) -> None:
        """Remove cached artifacts and the isolated local workspace."""
        self.cache.invalidate_prefix(self._prefix(reference))
        self.workspace_store.delete_workspace(reference.workspace_id)

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
