"""Controlled local workspace management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from shutil import rmtree
from tempfile import NamedTemporaryFile
from uuid import uuid4

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class InvalidWorkspaceIdentifier(ValueError):
    """Raised when an identifier could escape or corrupt the workspace root."""


@dataclass(frozen=True, slots=True)
class LocalWorkspaceStore:
    """Resolve local workspace paths without accepting arbitrary filesystem paths."""

    root: Path

    def prepare(self) -> Path:
        """Create and return the workspace root."""
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root.resolve()

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

    def write_result_bytes(
        self,
        *,
        workspace_id: str,
        result_id: str,
        payload: bytes,
    ) -> Path:
        """Write one uploaded result atomically inside a controlled workspace."""
        destination = self.result_path(workspace_id=workspace_id, result_id=result_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{result_id}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
        temporary.replace(destination)
        return destination

    def delete_workspace(self, workspace_id: str) -> None:
        """Delete one isolated workspace after validating its identifier."""
        path = self.workspace_path(workspace_id)
        if path.exists():
            rmtree(path)

    @staticmethod
    def _validate_identifier(value: str) -> None:
        if not _SAFE_ID.fullmatch(value):
            raise InvalidWorkspaceIdentifier(value)
