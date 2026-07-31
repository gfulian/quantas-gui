"""Filesystem-backed local process execution for scientific workflows."""

from __future__ import annotations

import importlib
import json
import multiprocessing
import os
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Protocol, cast
from uuid import uuid4

from filelock import FileLock, Timeout

from quantas_gui.services.backends import (
    ExecutionBackendDescriptor,
    JobEvent,
    JobHandle,
    JobState,
    JobStatus,
)
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.services.serialization import to_json_value
from quantas_gui.services.workspaces import LocalWorkspaceStore

_DEFAULT_HANDLERS: Mapping[str, str] = {
    "elasticity": "quantas_gui.workflows.elasticity.worker:run_elasticity_request",
}
_TERMINAL_STATES = frozenset({JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED})
_MAX_EVENT_BATCH = 1000


class WorkflowCancelled(RuntimeError):
    """Raised by a worker at a cooperative cancellation checkpoint."""


class WorkflowHandler(Protocol):
    """Callable contract implemented by one process-side workflow adapter."""

    def __call__(self, context: WorkflowExecutionContext) -> None:
        """Execute one request and write the native result to ``output_path``."""


@dataclass(frozen=True, slots=True)
class WorkflowExecutionContext:
    """Controlled resources exposed to a process-side workflow handler."""

    request_path: Path
    output_path: Path
    workspace_path: Path
    emit_callback: Callable[[str, str, float | None, Mapping[str, object]], None]
    cancellation_callback: Callable[[], bool]

    def emit(
        self,
        message: str,
        *,
        level: str = "info",
        progress: float | None = None,
        data: Mapping[str, object] | None = None,
    ) -> None:
        """Persist one bounded frontend-neutral event."""
        self.emit_callback(level, message, progress, data or {})

    def cancellation_requested(self) -> bool:
        """Return whether cancellation has been requested for this job."""
        return self.cancellation_callback()

    def checkpoint(self) -> None:
        """Stop at a safe workflow boundary when cancellation was requested."""
        if self.cancellation_requested():
            raise WorkflowCancelled("The calculation was cancelled.")


class LocalProcessExecutionBackend:
    """Run supported workflows in separate local processes.

    Job status and events are persisted below the controlled workspace so that
    browser refreshes and overlapping Dash callbacks do not own scientific
    state. The process table is intentionally local to one application process;
    server mode must inject a shared queue-backed implementation instead.
    """

    def __init__(
        self,
        workspace_store: LocalWorkspaceStore,
        *,
        handler_specs: Mapping[str, str] | None = None,
    ) -> None:
        self._workspace_store = workspace_store
        self._root = workspace_store.prepare()
        self._handler_specs = dict(_DEFAULT_HANDLERS if handler_specs is None else handler_specs)
        if not self._handler_specs:
            raise ValueError("at least one workflow handler must be configured")
        self._context = multiprocessing.get_context("spawn")
        self._processes: dict[str, BaseProcess] = {}
        self._process_guard = threading.RLock()

    @property
    def descriptor(self) -> ExecutionBackendDescriptor:
        """Return local worker capabilities without exposing process objects."""
        return ExecutionBackendDescriptor(
            kind="local-process",
            available=True,
            process_shared=False,
            supports_cancellation=True,
            detail="Separate local processes with filesystem-backed job state.",
        )

    def submit(
        self,
        *,
        module: str,
        request_path: Path,
        workspace_id: str,
    ) -> JobHandle:
        """Persist a queued job and start its worker process."""
        handler_spec = self._handler_specs.get(module)
        if handler_spec is None:
            raise ValueError(f"unsupported workflow module: {module}")

        workspace = self._workspace_store.workspace_path(workspace_id)
        resolved_request = request_path.resolve()
        try:
            relative_request = resolved_request.relative_to(workspace.resolve())
        except ValueError as exc:
            raise ValueError("request_path must be contained by its workspace") from exc
        if not resolved_request.is_file():
            raise FileNotFoundError("the persisted workflow request does not exist")

        job_id = uuid4().hex
        result_id = uuid4().hex
        handle = JobHandle(job_id=job_id, workspace_id=workspace_id)
        files = _JobFiles(
            root=self._root,
            workspace_id=workspace_id,
            job_id=job_id,
            lock_timeout_seconds=self._workspace_store.lock_timeout_seconds,
        )
        now = time.time()
        files.create(
            JobStatus(
                state=JobState.QUEUED,
                progress=0.0,
                message="Queued",
                submitted_at=now,
                updated_at=now,
            ),
            result_id=result_id,
        )
        files.append_event(level="info", message="Job queued", progress=0.0)

        process = self._context.Process(
            target=_run_local_job,
            args=(
                str(self._root),
                self._workspace_store.lock_timeout_seconds,
                module,
                handler_spec,
                job_id,
                workspace_id,
                relative_request.as_posix(),
                result_id,
            ),
            name=f"quantas-gui-{module}-{job_id[:8]}",
            daemon=True,
        )
        try:
            process.start()
        except Exception as exc:
            message = public_error_message(exc, fallback="The local worker could not start.")
            files.append_event(level="error", message=message)
            files.update_status(
                state=JobState.FAILED,
                message="Worker start failed",
                error=message,
                finished_at=time.time(),
            )
            raise RuntimeError(message) from exc
        with self._process_guard:
            self._processes[job_id] = process
        return handle

    def cancel(self, handle: JobHandle) -> None:
        """Request cooperative cancellation without terminating the process."""
        files = self._files(handle)
        status = self._reconcile_process(handle, files)
        if status.state in _TERMINAL_STATES:
            return
        files.request_cancellation()
        files.update_status(
            state=JobState.CANCELLING,
            message="Cancellation requested",
            cancel_requested=True,
        )
        files.append_event(level="warning", message="Cancellation requested")

    def status(self, handle: JobHandle) -> JobStatus:
        """Return the latest persisted status and detect an unhandled worker exit."""
        return self._reconcile_process(handle, self._files(handle))

    def events(
        self,
        handle: JobHandle,
        *,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> Sequence[JobEvent]:
        """Return ordered events newer than the supplied cursor."""
        files = self._files(handle)
        self._reconcile_process(handle, files)
        return files.read_events(after_sequence=after_sequence, limit=limit)

    def _files(self, handle: JobHandle) -> _JobFiles:
        return _JobFiles(
            root=self._root,
            workspace_id=handle.workspace_id,
            job_id=handle.job_id,
            lock_timeout_seconds=self._workspace_store.lock_timeout_seconds,
        )

    def _reconcile_process(self, handle: JobHandle, files: _JobFiles) -> JobStatus:
        status = files.read_status()
        with self._process_guard:
            process = self._processes.get(handle.job_id)
        if process is not None and process.exitcode is not None:
            process.join(timeout=0)
            if status.state not in _TERMINAL_STATES:
                cleanup_error = self._cleanup_interrupted_output(handle, files)
                message = f"The worker process exited unexpectedly with code {process.exitcode}."
                if cleanup_error is not None:
                    message += " Partial output cleanup could not be confirmed."
                files.append_event(level="error", message=message)
                status = files.update_status(
                    state=JobState.FAILED,
                    message="Worker process crashed",
                    error=message,
                    finished_at=time.time(),
                )
            with self._process_guard:
                self._processes.pop(handle.job_id, None)
        return status

    def _cleanup_interrupted_output(
        self,
        handle: JobHandle,
        files: _JobFiles,
    ) -> str | None:
        try:
            result_id = files.read_planned_result_id()
            destination = self._workspace_store.result_path(
                workspace_id=handle.workspace_id,
                result_id=result_id,
            )
            self._workspace_store.cleanup_output(destination)
        except Exception as exc:
            return public_error_message(
                exc,
                fallback="Interrupted output cleanup failed.",
            )
        return None


@dataclass(frozen=True, slots=True)
class _JobFiles:
    root: Path
    workspace_id: str
    job_id: str
    lock_timeout_seconds: float

    @property
    def workspace(self) -> Path:
        return self.root / self.workspace_id

    @property
    def directory(self) -> Path:
        return self.workspace / "jobs" / self.job_id

    @property
    def status_path(self) -> Path:
        return self.directory / "status.json"

    @property
    def events_path(self) -> Path:
        return self.directory / "events.jsonl"

    @property
    def metadata_path(self) -> Path:
        return self.directory / "job.json"

    @property
    def cancellation_path(self) -> Path:
        return self.directory / "cancel.requested"

    @property
    def lock_path(self) -> Path:
        return self.directory / ".state.lock"

    def create(self, status: JobStatus, *, result_id: str) -> None:
        self.directory.mkdir(parents=True, exist_ok=False)
        self.events_path.touch()
        with self.metadata_path.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump({"result_id": result_id}, stream, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        self._write_status_unlocked(status)

    def read_planned_result_id(self) -> str:
        with self.locked():
            with self.metadata_path.open("r", encoding="utf-8") as stream:
                value = json.load(stream)
            if not isinstance(value, Mapping):
                raise ValueError("persisted job metadata must be a mapping")
            result_id = value.get("result_id")
            if not isinstance(result_id, str):
                raise ValueError("persisted job metadata has no result identifier")
            return result_id

    def read_status(self) -> JobStatus:
        with self.locked():
            return self._read_status_unlocked()

    def update_status(
        self,
        *,
        state: JobState | None = None,
        progress: float | None = None,
        message: str | None = None,
        result_id: str | None = None,
        started_at: float | None = None,
        finished_at: float | None = None,
        cancel_requested: bool | None = None,
        error: str | None = None,
    ) -> JobStatus:
        with self.locked():
            current = self._read_status_unlocked()
            resolved_progress = current.progress
            if progress is not None:
                resolved_progress = max(current.progress or 0.0, progress)
            updated = replace(
                current,
                state=current.state if state is None else state,
                progress=resolved_progress,
                message=current.message if message is None else message,
                result_id=current.result_id if result_id is None else result_id,
                started_at=current.started_at if started_at is None else started_at,
                updated_at=time.time(),
                finished_at=current.finished_at if finished_at is None else finished_at,
                cancel_requested=(
                    current.cancel_requested if cancel_requested is None else cancel_requested
                ),
                error=current.error if error is None else error,
            )
            self._write_status_unlocked(updated)
            return updated

    def append_event(
        self,
        *,
        level: str,
        message: str,
        progress: float | None = None,
        data: Mapping[str, object] | None = None,
    ) -> JobEvent:
        with self.locked():
            status = self._read_status_unlocked()
            sequence = status.next_event_sequence + 1
            created_at = time.time()
            normalized_data = to_json_value(dict(data or {}))
            if not isinstance(normalized_data, Mapping):
                normalized_data = {}
            event = JobEvent(
                sequence=sequence,
                created_at=created_at,
                level=level,
                message=message,
                progress=progress,
                data=cast(Mapping[str, object], normalized_data),
            )
            with self.events_path.open("a", encoding="utf-8", newline="\n") as stream:
                json.dump(event.as_dict(), stream, ensure_ascii=False, separators=(",", ":"))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            resolved_progress = status.progress
            if progress is not None:
                resolved_progress = max(status.progress or 0.0, progress)
            self._write_status_unlocked(
                replace(
                    status,
                    progress=resolved_progress,
                    message=message,
                    updated_at=created_at,
                    next_event_sequence=sequence,
                )
            )
            return event

    def read_events(self, *, after_sequence: int, limit: int) -> tuple[JobEvent, ...]:
        if after_sequence < 0:
            raise ValueError("after_sequence must not be negative")
        if limit < 1:
            raise ValueError("limit must be positive")
        bounded_limit = min(limit, _MAX_EVENT_BATCH)
        with self.locked():
            records: list[JobEvent] = []
            with self.events_path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    event = JobEvent.from_dict(json.loads(line))
                    if event.sequence > after_sequence:
                        records.append(event)
                        if len(records) >= bounded_limit:
                            break
            return tuple(records)

    def request_cancellation(self) -> None:
        with self.locked():
            self.cancellation_path.touch(exist_ok=True)

    def cancellation_requested(self) -> bool:
        return self.cancellation_path.exists()

    @contextmanager
    def locked(self) -> Iterator[None]:
        lock = FileLock(str(self.lock_path))
        try:
            with lock.acquire(timeout=self.lock_timeout_seconds):
                yield
        except Timeout as exc:
            raise TimeoutError(f"job {self.job_id!r} remained busy") from exc

    def _read_status_unlocked(self) -> JobStatus:
        if not self.status_path.is_file():
            raise FileNotFoundError("the requested job does not exist")
        with self.status_path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
        if not isinstance(value, Mapping):
            raise ValueError("persisted job status must be a mapping")
        return JobStatus.from_dict(value)

    def _write_status_unlocked(self, status: JobStatus) -> None:
        temporary = self.status_path.with_name(f".{self.status_path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as stream:
                json.dump(status.as_dict(), stream, ensure_ascii=False, separators=(",", ":"))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.status_path)
        finally:
            temporary.unlink(missing_ok=True)


def _run_local_job(
    root: str,
    lock_timeout_seconds: float,
    module: str,
    handler_spec: str,
    job_id: str,
    workspace_id: str,
    relative_request: str,
    result_id: str,
) -> None:
    """Child-process entry point. All exceptions become persistent job state."""
    workspace_store = LocalWorkspaceStore(Path(root), lock_timeout_seconds=lock_timeout_seconds)
    files = _JobFiles(
        root=Path(root),
        workspace_id=workspace_id,
        job_id=job_id,
        lock_timeout_seconds=lock_timeout_seconds,
    )
    destination = workspace_store.result_path(workspace_id=workspace_id, result_id=result_id)

    def cleanup_output() -> str | None:
        try:
            workspace_store.cleanup_output(destination)
        except Exception as exc:
            return public_error_message(
                exc,
                fallback="Incomplete output cleanup failed.",
            )
        return None

    def emit(
        level: str,
        message: str,
        progress: float | None,
        data: Mapping[str, object],
    ) -> None:
        files.append_event(level=level, message=message, progress=progress, data=data)

    try:
        if files.cancellation_requested():
            raise WorkflowCancelled("The calculation was cancelled before it started.")
        started_at = time.time()
        files.update_status(
            state=JobState.RUNNING,
            progress=0.0,
            message="Running",
            started_at=started_at,
        )
        files.append_event(level="info", message="Worker started", progress=0.0)
        handler = _resolve_handler(handler_spec)
        request_path = (files.workspace / Path(relative_request)).resolve()
        if not request_path.is_relative_to(files.workspace.resolve()):
            raise ValueError("the persisted request escaped its workspace")

        with workspace_store.atomic_output(destination) as temporary_output:
            context = WorkflowExecutionContext(
                request_path=request_path,
                output_path=temporary_output,
                workspace_path=files.workspace,
                emit_callback=emit,
                cancellation_callback=files.cancellation_requested,
            )
            context.checkpoint()
            handler(context)
            context.checkpoint()

        if files.cancellation_requested():
            raise WorkflowCancelled("The calculation was cancelled before publication.")

        files.append_event(
            level="result",
            message="Native Quantas result published",
            progress=1.0,
            data={"module": module, "result_id": result_id},
        )
        files.update_status(
            state=JobState.SUCCEEDED,
            progress=1.0,
            message="Completed",
            result_id=result_id,
            finished_at=time.time(),
        )
    except WorkflowCancelled as exc:
        message = public_error_message(exc, fallback="The calculation was cancelled.")
        cleanup_error = cleanup_output()
        if cleanup_error is None:
            files.append_event(level="warning", message=message)
            files.update_status(
                state=JobState.CANCELLED,
                message="Cancelled",
                cancel_requested=True,
                finished_at=time.time(),
                error=None,
            )
        else:
            error = f"{message} Incomplete output cleanup could not be confirmed: {cleanup_error}"
            files.append_event(level="error", message=error)
            files.update_status(
                state=JobState.FAILED,
                message="Cancellation cleanup failed",
                cancel_requested=True,
                error=error,
                finished_at=time.time(),
            )
    except BaseException as exc:
        message = public_error_message(exc)
        cleanup_error = cleanup_output()
        if cleanup_error is not None:
            message += f" Incomplete output cleanup could not be confirmed: {cleanup_error}"
        files.append_event(level="error", message=message)
        files.update_status(
            state=JobState.FAILED,
            message="Failed",
            error=message,
            finished_at=time.time(),
        )


def _resolve_handler(specification: str) -> WorkflowHandler:
    module_name, separator, attribute_name = specification.partition(":")
    if not separator or not module_name or not attribute_name:
        raise ValueError(f"invalid workflow handler specification: {specification!r}")
    module = importlib.import_module(module_name)
    handler = getattr(module, attribute_name)
    if not callable(handler):
        raise TypeError(f"workflow handler is not callable: {specification!r}")
    return cast(WorkflowHandler, handler)


__all__ = [
    "LocalProcessExecutionBackend",
    "WorkflowCancelled",
    "WorkflowExecutionContext",
    "WorkflowHandler",
]
