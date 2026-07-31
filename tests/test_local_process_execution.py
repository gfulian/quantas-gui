from __future__ import annotations

import json
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from quantas_gui.services.backends import JobHandle, JobState
from quantas_gui.services.local_execution import LocalProcessExecutionBackend
from quantas_gui.services.workspaces import LocalWorkspaceStore

_TERMINAL = {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}


@pytest.fixture
def handler_module(tmp_path: Path) -> Iterator[str]:
    module_path = tmp_path / "quantas_gui_test_workers.py"
    module_path.write_text(
        """
import json
import os
import time


def success(context):
    value = json.loads(context.request_path.read_text(encoding="utf-8"))
    for index in range(1, 4):
        context.checkpoint()
        context.emit(
            f"step {index}",
            level="progress",
            progress=index / 4.0,
            data={"job": value["job"]},
        )
        time.sleep(0.03)
    context.output_path.write_text(value["job"], encoding="utf-8")


def slow(context):
    for index in range(200):
        context.checkpoint()
        context.emit(
            "working",
            level="progress",
            progress=min(0.9, index / 220.0),
        )
        time.sleep(0.02)
    context.output_path.write_text("late result", encoding="utf-8")


def crash(context):
    context.output_path.write_text("partial", encoding="utf-8")
    os._exit(7)


def fail(context):
    del context
    raise RuntimeError(r"failed while reading C:\\private\\sample.dat")
""".lstrip(),
        encoding="utf-8",
    )
    sys.path.insert(0, str(tmp_path))
    try:
        yield "quantas_gui_test_workers"
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("quantas_gui_test_workers", None)


def _request(store: LocalWorkspaceStore, workspace_id: str, job: str) -> Path:
    destination = store.workspace_path(workspace_id) / "requests" / "request.json"
    with store.atomic_output(destination) as temporary:
        temporary.write_text(json.dumps({"job": job}), encoding="utf-8")
    return destination


def _wait(
    backend: LocalProcessExecutionBackend,
    handle: JobHandle,
    *,
    timeout: float = 15.0,
):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = backend.status(handle)
        if status.state in _TERMINAL:
            return status
        time.sleep(0.03)
    raise AssertionError(f"job did not finish: {backend.status(handle)}")


@contextmanager
def _backend(tmp_path: Path, module: str, handler: str):
    store = LocalWorkspaceStore(tmp_path / "workspaces", lock_timeout_seconds=5.0)
    backend = LocalProcessExecutionBackend(
        store,
        handler_specs={module: handler},
    )
    yield store, backend


def test_local_process_job_persists_monotonic_events_and_atomic_result(
    tmp_path: Path,
    handler_module: str,
) -> None:
    with _backend(tmp_path, "test", f"{handler_module}:success") as (store, backend):
        workspace_id = store.create_workspace()
        handle = backend.submit(
            module="test",
            request_path=_request(store, workspace_id, "alpha"),
            workspace_id=workspace_id,
        )
        status = _wait(backend, handle)

        assert status.state is JobState.SUCCEEDED
        assert status.progress == 1.0
        assert status.result_id is not None
        assert (
            store.result_path(
                workspace_id=workspace_id,
                result_id=status.result_id,
            ).read_text(encoding="utf-8")
            == "alpha"
        )
        events = backend.events(handle)
        assert [event.sequence for event in events] == list(range(1, len(events) + 1))
        progress = [event.progress for event in events if event.progress is not None]
        assert progress == sorted(progress)
        assert backend.events(handle, after_sequence=events[-2].sequence) == (events[-1],)


def test_persisted_job_can_be_polled_by_a_recreated_local_backend(
    tmp_path: Path,
    handler_module: str,
) -> None:
    store = LocalWorkspaceStore(tmp_path / "workspaces", lock_timeout_seconds=5.0)
    first_backend = LocalProcessExecutionBackend(
        store,
        handler_specs={"test": f"{handler_module}:success"},
    )
    workspace_id = store.create_workspace()
    handle = first_backend.submit(
        module="test",
        request_path=_request(store, workspace_id, "reopened"),
        workspace_id=workspace_id,
    )

    recreated_backend = LocalProcessExecutionBackend(
        store,
        handler_specs={"test": f"{handler_module}:success"},
    )
    status = _wait(recreated_backend, handle)

    assert status.state is JobState.SUCCEEDED
    assert status.result_id is not None
    assert recreated_backend.events(handle)


def test_local_process_cancellation_removes_partial_output(
    tmp_path: Path,
    handler_module: str,
) -> None:
    with _backend(tmp_path, "test", f"{handler_module}:slow") as (store, backend):
        workspace_id = store.create_workspace()
        handle = backend.submit(
            module="test",
            request_path=_request(store, workspace_id, "cancel"),
            workspace_id=workspace_id,
        )
        deadline = time.monotonic() + 5.0
        while backend.status(handle).state is JobState.QUEUED and time.monotonic() < deadline:
            time.sleep(0.02)
        backend.cancel(handle)
        status = _wait(backend, handle)

        assert status.state is JobState.CANCELLED
        assert status.cancel_requested is True
        assert status.result_id is None
        assert not list((store.workspace_path(workspace_id) / "results").glob("*.hdf5"))


def test_local_process_detects_hard_worker_crash(
    tmp_path: Path,
    handler_module: str,
) -> None:
    with _backend(tmp_path, "test", f"{handler_module}:crash") as (store, backend):
        workspace_id = store.create_workspace()
        handle = backend.submit(
            module="test",
            request_path=_request(store, workspace_id, "crash"),
            workspace_id=workspace_id,
        )
        status = _wait(backend, handle)

        assert status.state is JobState.FAILED
        assert status.error is not None
        assert "code 7" in status.error
        results = store.workspace_path(workspace_id) / "results"
        assert not list(results.iterdir())


def test_local_process_sanitizes_worker_errors(
    tmp_path: Path,
    handler_module: str,
) -> None:
    with _backend(tmp_path, "test", f"{handler_module}:fail") as (store, backend):
        workspace_id = store.create_workspace()
        handle = backend.submit(
            module="test",
            request_path=_request(store, workspace_id, "fail"),
            workspace_id=workspace_id,
        )
        status = _wait(backend, handle)

        assert status.state is JobState.FAILED
        assert status.error is not None
        assert "<server path>" in status.error
        assert "private" not in status.error


def test_two_local_jobs_do_not_share_workspace_or_result(
    tmp_path: Path,
    handler_module: str,
) -> None:
    with _backend(tmp_path, "test", f"{handler_module}:success") as (store, backend):
        first_workspace = store.create_workspace()
        second_workspace = store.create_workspace()
        first = backend.submit(
            module="test",
            request_path=_request(store, first_workspace, "first"),
            workspace_id=first_workspace,
        )
        second = backend.submit(
            module="test",
            request_path=_request(store, second_workspace, "second"),
            workspace_id=second_workspace,
        )
        first_status = _wait(backend, first)
        second_status = _wait(backend, second)

        assert first_status.state is second_status.state is JobState.SUCCEEDED
        assert first.workspace_id != second.workspace_id
        assert first_status.result_id != second_status.result_id
        assert (
            store.result_path(
                workspace_id=first.workspace_id,
                result_id=first_status.result_id or "missing",
            ).read_text(encoding="utf-8")
            == "first"
        )
        assert (
            store.result_path(
                workspace_id=second.workspace_id,
                result_id=second_status.result_id or "missing",
            ).read_text(encoding="utf-8")
            == "second"
        )
