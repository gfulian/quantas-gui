"""Deployment-neutral job and result service contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Protocol


class JobState(str, Enum):
    """Serializable lifecycle states shared by local and remote workers."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class JobHandle:
    """Stable identifiers returned to Dash callbacks."""

    job_id: str
    workspace_id: str


@dataclass(frozen=True, slots=True)
class JobStatus:
    """Serializable status snapshot for progress components."""

    state: JobState
    progress: float | None = None
    message: str | None = None
    result_id: str | None = None


class ExecutionBackend(Protocol):
    """Run Quantas work without exposing worker implementation details."""

    def submit(
        self,
        *,
        module: str,
        request_path: Path,
        workspace_id: str,
    ) -> JobHandle:
        """Submit a calculation and return a stable handle."""

    def cancel(self, handle: JobHandle) -> None:
        """Request cancellation of a running calculation."""

    def status(self, handle: JobHandle) -> JobStatus:
        """Return a progress and state snapshot."""


class ResultStore(Protocol):
    """Persist large Quantas results outside the browser session."""

    def result_path(self, *, workspace_id: str, result_id: str) -> Path:
        """Resolve an internal result identifier to a controlled path."""

    def metadata(self, *, workspace_id: str, result_id: str) -> Mapping[str, object]:
        """Return lightweight, JSON-compatible result metadata."""
