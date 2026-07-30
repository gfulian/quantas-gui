"""Deployment-neutral job and result service contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class JobState(str, Enum):
    """Serializable lifecycle states shared by local and remote workers."""

    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class JobHandle:
    """Stable opaque identifiers returned to Dash callbacks."""

    job_id: str
    workspace_id: str

    def __post_init__(self) -> None:
        for label, value in (("job_id", self.job_id), ("workspace_id", self.workspace_id)):
            if not _OPAQUE_ID.fullmatch(value):
                raise ValueError(f"invalid {label}")

    def as_dict(self) -> dict[str, str]:
        """Return the lightweight browser representation."""
        return {"job_id": self.job_id, "workspace_id": self.workspace_id}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> JobHandle:
        """Restore and validate a browser representation."""
        return cls(job_id=str(value["job_id"]), workspace_id=str(value["workspace_id"]))


@dataclass(frozen=True, slots=True)
class JobEvent:
    """One bounded frontend-neutral event emitted by a background job."""

    sequence: int
    created_at: float
    level: str
    message: str
    progress: float | None = None
    data: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("event sequence must not be negative")
        if not self.level.strip():
            raise ValueError("event level must not be empty")
        if not self.message.strip():
            raise ValueError("event message must not be empty")
        _validate_progress(self.progress)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible event representation."""
        return {
            "sequence": self.sequence,
            "created_at": self.created_at,
            "level": self.level,
            "message": self.message,
            "progress": self.progress,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> JobEvent:
        """Restore and validate a persisted event representation."""
        data = value.get("data", {})
        if not isinstance(data, Mapping):
            raise ValueError("event data must be a mapping")
        progress = value.get("progress")
        return cls(
            sequence=int(value["sequence"]),
            created_at=float(value["created_at"]),
            level=str(value["level"]),
            message=str(value["message"]),
            progress=None if progress is None else float(progress),
            data=dict(data),
        )


@dataclass(frozen=True, slots=True)
class JobStatus:
    """Serializable status snapshot for polling and progress components."""

    state: JobState
    progress: float | None = None
    message: str | None = None
    result_id: str | None = None
    submitted_at: float | None = None
    started_at: float | None = None
    updated_at: float | None = None
    finished_at: float | None = None
    cancel_requested: bool = False
    error: str | None = None
    next_event_sequence: int = 0

    def __post_init__(self) -> None:
        _validate_progress(self.progress)
        if self.next_event_sequence < 0:
            raise ValueError("next_event_sequence must not be negative")
        if self.result_id is not None and not _OPAQUE_ID.fullmatch(self.result_id):
            raise ValueError("invalid result_id")

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible status snapshot."""
        return {
            "state": self.state.value,
            "progress": self.progress,
            "message": self.message,
            "result_id": self.result_id,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "finished_at": self.finished_at,
            "cancel_requested": self.cancel_requested,
            "error": self.error,
            "next_event_sequence": self.next_event_sequence,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> JobStatus:
        """Restore and validate a persisted status snapshot."""
        progress = value.get("progress")
        return cls(
            state=JobState(str(value["state"])),
            progress=None if progress is None else float(progress),
            message=_optional_string(value.get("message")),
            result_id=_optional_string(value.get("result_id")),
            submitted_at=_optional_float(value.get("submitted_at")),
            started_at=_optional_float(value.get("started_at")),
            updated_at=_optional_float(value.get("updated_at")),
            finished_at=_optional_float(value.get("finished_at")),
            cancel_requested=_optional_bool(value.get("cancel_requested"), default=False),
            error=_optional_string(value.get("error")),
            next_event_sequence=int(value.get("next_event_sequence", 0)),
        )


@dataclass(frozen=True, slots=True)
class ExecutionBackendDescriptor:
    """Capabilities surfaced without exposing the worker implementation."""

    kind: str
    available: bool
    process_shared: bool
    supports_cancellation: bool
    detail: str


class ExecutionBackend(Protocol):
    """Run Quantas work outside Dash request callbacks.

    Implementations must persist job state independently of the browser. Local
    mode may use a process-backed worker; server mode is expected to inject a
    queue-backed implementation whose state is shared by every WSGI worker.
    """

    @property
    def descriptor(self) -> ExecutionBackendDescriptor:
        """Return immutable backend capabilities."""

    def submit(
        self,
        *,
        module: str,
        request_path: Path,
        workspace_id: str,
    ) -> JobHandle:
        """Submit a calculation and return a stable handle."""

    def cancel(self, handle: JobHandle) -> None:
        """Request cooperative cancellation of a queued or running job."""

    def status(self, handle: JobHandle) -> JobStatus:
        """Return the latest persistent progress and state snapshot."""

    def events(
        self,
        handle: JobHandle,
        *,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> Sequence[JobEvent]:
        """Return bounded events newer than ``after_sequence``."""


@dataclass(frozen=True, slots=True)
class DisabledExecutionBackend:
    """Explicit placeholder used before executable workflows are enabled."""

    reason: str = "Scientific workflow execution is not enabled in this milestone."

    @property
    def descriptor(self) -> ExecutionBackendDescriptor:
        return ExecutionBackendDescriptor(
            kind="disabled",
            available=False,
            process_shared=False,
            supports_cancellation=False,
            detail=self.reason,
        )

    def submit(self, *, module: str, request_path: Path, workspace_id: str) -> JobHandle:
        del module, request_path, workspace_id
        raise RuntimeError(self.reason)

    def cancel(self, handle: JobHandle) -> None:
        del handle
        raise RuntimeError(self.reason)

    def status(self, handle: JobHandle) -> JobStatus:
        del handle
        raise RuntimeError(self.reason)

    def events(
        self,
        handle: JobHandle,
        *,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> Sequence[JobEvent]:
        del handle, after_sequence, limit
        raise RuntimeError(self.reason)


def _validate_progress(value: float | None) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError("progress must be between 0 and 1")


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("expected a string or null")
    return value


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("expected a number, numeric string, or null")
    return float(value)


def _optional_bool(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError("expected a boolean")
    return value


class ResultStore(Protocol):
    """Persist large Quantas results outside the browser session."""

    def result_path(self, *, workspace_id: str, result_id: str) -> Path:
        """Resolve an internal result identifier to a controlled path."""

    def metadata(self, *, workspace_id: str, result_id: str) -> Mapping[str, object]:
        """Return lightweight, JSON-compatible result metadata."""
