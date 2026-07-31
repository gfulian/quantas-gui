"""Controlled workspace management for local and shared-filesystem deployments."""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from os import fsync
from pathlib import Path
from shutil import rmtree
from tempfile import NamedTemporaryFile
from typing import Protocol
from uuid import uuid4

from filelock import FileLock, Timeout

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class InvalidWorkspaceIdentifier(ValueError):
    """Raised when an identifier could escape or corrupt the workspace root."""


class WorkspaceBusyError(TimeoutError):
    """Raised when a concurrent workspace operation exceeds the lock timeout."""


class WorkspaceClosingError(FileNotFoundError):
    """Raised when a workspace has entered irreversible deletion."""


class WorkspaceStore(Protocol):
    """Controlled filesystem operations required by application services."""

    def prepare(self) -> Path:
        """Create and return the workspace root."""

    def create_workspace(self) -> str:
        """Create an isolated workspace and return its opaque identifier."""

    def workspace_path(self, workspace_id: str) -> Path:
        """Resolve a validated workspace identifier."""

    def result_path(self, *, workspace_id: str, result_id: str) -> Path:
        """Resolve a validated result identifier."""

    def export_path(self, *, workspace_id: str, result_id: str, filename: str) -> Path:
        """Resolve a controlled derived-export path."""

    def write_result_bytes(
        self,
        *,
        workspace_id: str,
        result_id: str,
        payload: bytes,
    ) -> Path:
        """Write one result atomically."""

    def result_access(self, *, workspace_id: str, result_id: str) -> AbstractContextManager[Path]:
        """Access a result unless its workspace is closing or absent."""

    def atomic_output(self, destination: Path) -> AbstractContextManager[Path]:
        """Yield a temporary output and atomically publish it on success."""

    def cleanup_output(self, destination: Path) -> None:
        """Remove a final output and matching unpublished temporary files."""

    def delete_workspace(self, workspace_id: str) -> None:
        """Delete a workspace after concurrent users have released it."""


@dataclass(frozen=True, slots=True)
class LocalWorkspaceStore:
    """Filesystem workspace store with portable cross-process locking.

    One lock file is retained outside each workspace directory. This allows a
    close operation to wait for active HDF5 readers before deleting a disposable
    workspace. The lock also makes atomic writes and derived exports safe when
    several WSGI workers share the same workspace root.
    """

    root: Path
    lock_timeout_seconds: float = 300.0

    def __post_init__(self) -> None:
        if self.lock_timeout_seconds <= 0:
            raise ValueError("lock_timeout_seconds must be positive")

    def prepare(self) -> Path:
        """Create and return the workspace root and lock directory."""
        self.root.mkdir(parents=True, exist_ok=True)
        resolved = self.root.resolve()
        (resolved / ".locks").mkdir(parents=True, exist_ok=True)
        return resolved

    def create_workspace(self) -> str:
        """Create an isolated workspace and return its opaque identifier."""
        workspace_id = uuid4().hex
        self.workspace_path(workspace_id).mkdir(parents=True, exist_ok=False)
        return workspace_id

    def workspace_path(self, workspace_id: str) -> Path:
        """Return a validated path contained by the configured root."""
        self._validate_identifier(workspace_id)
        root = self.prepare()
        path = (root / workspace_id).resolve()
        if path.parent != root:
            raise InvalidWorkspaceIdentifier(workspace_id)
        return path

    def result_path(self, *, workspace_id: str, result_id: str) -> Path:
        """Return a validated HDF5 result path inside a workspace."""
        self._validate_identifier(result_id)
        return self.workspace_path(workspace_id) / "results" / f"{result_id}.hdf5"

    def export_path(
        self,
        *,
        workspace_id: str,
        result_id: str,
        filename: str,
    ) -> Path:
        """Return a controlled derived-export path inside one workspace."""
        self._validate_identifier(result_id)
        safe_name = _safe_filename(filename)
        directory = self.workspace_path(workspace_id) / "exports" / result_id
        path = (directory / safe_name[:240]).resolve()
        if path.parent != directory.resolve():
            raise InvalidWorkspaceIdentifier(filename)
        return path

    def write_result_bytes(
        self,
        *,
        workspace_id: str,
        result_id: str,
        payload: bytes,
    ) -> Path:
        """Write one uploaded result atomically inside a controlled workspace."""
        with self._workspace_access(workspace_id):
            destination = self.result_path(workspace_id=workspace_id, result_id=result_id)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = _temporary_path(destination)
            try:
                with temporary.open("wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    fsync(handle.fileno())
                temporary.replace(destination)
            finally:
                temporary.unlink(missing_ok=True)
            return destination

    @contextmanager
    def result_access(self, *, workspace_id: str, result_id: str) -> Iterator[Path]:
        """Hold one workspace lock while a native result is read or inspected."""
        with self._workspace_access(workspace_id):
            yield self.result_path(workspace_id=workspace_id, result_id=result_id)

    @contextmanager
    def atomic_output(self, destination: Path) -> Iterator[Path]:
        """Publish one derived file atomically under its workspace lock."""
        resolved = destination.resolve()
        root = self.prepare()
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise InvalidWorkspaceIdentifier(str(destination)) from exc
        if len(relative.parts) < 2:
            raise InvalidWorkspaceIdentifier(str(destination))
        workspace_id = relative.parts[0]
        self._validate_identifier(workspace_id)

        with self._workspace_access(workspace_id):
            workspace = self.workspace_path(workspace_id)
            if not workspace.is_dir():
                raise FileNotFoundError("the workspace is no longer available")
            resolved.parent.mkdir(parents=True, exist_ok=True)
            temporary = _temporary_path(resolved)
            try:
                yield temporary
                if not temporary.is_file():
                    raise FileNotFoundError("the export writer did not create its output")
                _sync_file(temporary)
                temporary.replace(resolved)
            finally:
                temporary.unlink(missing_ok=True)

    def cleanup_output(self, destination: Path) -> None:
        """Remove one controlled output and remnants from interrupted publication."""
        resolved = destination.resolve()
        root = self.prepare()
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise InvalidWorkspaceIdentifier(str(destination)) from exc
        if len(relative.parts) < 2:
            raise InvalidWorkspaceIdentifier(str(destination))
        workspace_id = relative.parts[0]
        self._validate_identifier(workspace_id)

        with self._workspace_access(workspace_id):
            resolved.unlink(missing_ok=True)
            pattern = f".{resolved.stem}.*.tmp{resolved.suffix}"
            for temporary in resolved.parent.glob(pattern):
                temporary.unlink(missing_ok=True)

    def delete_workspace(self, workspace_id: str) -> None:
        """Mark a workspace closing, then delete it after active readers finish."""
        path = self.workspace_path(workspace_id)
        if not path.exists():
            return
        marker = path / ".closing"
        try:
            marker.touch(exist_ok=True)
        except FileNotFoundError:
            return
        with self._workspace_access(workspace_id, allow_closing=True):
            if path.exists():
                rmtree(path)

    @contextmanager
    def _workspace_access(
        self,
        workspace_id: str,
        *,
        allow_closing: bool = False,
    ) -> Iterator[None]:
        self._validate_identifier(workspace_id)
        lock = FileLock(str(self._lock_path(workspace_id)))
        try:
            with lock.acquire(timeout=self.lock_timeout_seconds):
                workspace = self.workspace_path(workspace_id)
                if not workspace.is_dir():
                    raise FileNotFoundError("the workspace is no longer available")
                if not allow_closing and (workspace / ".closing").exists():
                    raise WorkspaceClosingError("the workspace is closing")
                yield
        except Timeout as exc:
            raise WorkspaceBusyError(
                f"workspace {workspace_id!r} remained busy for "
                f"{self.lock_timeout_seconds:g} seconds"
            ) from exc

    def _lock_path(self, workspace_id: str) -> Path:
        return self.prepare() / ".locks" / f"{workspace_id}.lock"

    @staticmethod
    def _validate_identifier(value: str) -> None:
        if not _SAFE_ID.fullmatch(value):
            raise InvalidWorkspaceIdentifier(value)


def _safe_filename(filename: str) -> str:
    safe_name = Path(str(filename).replace("\\", "/")).name.strip()
    if not safe_name or safe_name in {".", ".."}:
        raise InvalidWorkspaceIdentifier(filename)
    safe_name = "".join(
        character if character.isalnum() or character in {"-", "_", "."} else "-"
        for character in safe_name
    )
    safe_name = "-".join(part for part in safe_name.split("-") if part)
    if not safe_name:
        raise InvalidWorkspaceIdentifier(filename)
    return safe_name


def _sync_file(path: Path) -> None:
    """Flush a completed file through a descriptor accepted on all platforms.

    Windows rejects ``os.fsync`` on a descriptor opened read-only. Reopening the
    completed temporary file in append-binary mode gives ``fsync`` a writable
    descriptor without changing the file contents.
    """
    with path.open("ab") as handle:
        handle.flush()
        fsync(handle.fileno())


def _temporary_path(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = destination.suffix
    with NamedTemporaryFile(
        mode="wb",
        dir=destination.parent,
        prefix=f".{destination.stem}.",
        suffix=f".tmp{suffix}",
        delete=False,
    ) as handle:
        return Path(handle.name)
