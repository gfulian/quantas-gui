from __future__ import annotations

from pathlib import Path

import pytest

from quantas_gui.services.workspaces import (
    InvalidWorkspaceIdentifier,
    LocalWorkspaceStore,
)


def test_workspace_and_result_paths_remain_under_root(tmp_path: Path) -> None:
    store = LocalWorkspaceStore(tmp_path)
    workspace_id = store.create_workspace()
    result = store.result_path(workspace_id=workspace_id, result_id="result-001")
    assert result == tmp_path.resolve() / workspace_id / "results" / "result-001.hdf5"


@pytest.mark.parametrize("identifier", ["../escape", "/absolute", "", "a/b", ".."])
def test_invalid_identifiers_are_rejected(tmp_path: Path, identifier: str) -> None:
    store = LocalWorkspaceStore(tmp_path)
    with pytest.raises(InvalidWorkspaceIdentifier):
        store.workspace_path(identifier)


def test_export_path_is_sanitized_and_contained(tmp_path: Path) -> None:
    store = LocalWorkspaceStore(tmp_path)
    workspace_id = store.create_workspace()
    path = store.export_path(
        workspace_id=workspace_id,
        result_id="result-001",
        filename=r"..\unsafe table.csv",
    )
    assert path == tmp_path.resolve() / workspace_id / "exports" / "result-001" / "unsafe-table.csv"


def test_delete_waits_for_active_result_access(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import sleep

    store = LocalWorkspaceStore(tmp_path, lock_timeout_seconds=2)
    workspace_id = store.create_workspace()
    store.write_result_bytes(
        workspace_id=workspace_id,
        result_id="result-001",
        payload=b"result",
    )
    deletion_started = Event()

    def delete() -> None:
        deletion_started.set()
        store.delete_workspace(workspace_id)

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        with store.result_access(workspace_id=workspace_id, result_id="result-001") as path:
            future = executor.submit(delete)
            assert deletion_started.wait(timeout=1)
            sleep(0.05)
            assert path.is_file()
        assert future.result(timeout=2) is None
    finally:
        executor.shutdown(wait=True)
    assert not store.workspace_path(workspace_id).exists()


def test_atomic_output_publishes_only_complete_files(tmp_path: Path) -> None:
    store = LocalWorkspaceStore(tmp_path)
    workspace_id = store.create_workspace()
    destination = store.export_path(
        workspace_id=workspace_id,
        result_id="result-001",
        filename="table.csv",
    )

    with store.atomic_output(destination) as temporary:
        temporary.write_text("complete\n", encoding="utf-8")
        assert not destination.exists()

    assert destination.read_text(encoding="utf-8") == "complete\n"


def test_atomic_output_syncs_through_a_writable_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = LocalWorkspaceStore(tmp_path)
    workspace_id = store.create_workspace()
    destination = store.export_path(
        workspace_id=workspace_id,
        result_id="result-001",
        filename="table.csv",
    )
    descriptor_is_writable: list[bool] = []

    def record_fsync(file_descriptor: int) -> None:
        import os

        os.write(file_descriptor, b"")
        descriptor_is_writable.append(True)

    monkeypatch.setattr("quantas_gui.services.workspaces.fsync", record_fsync)

    with store.atomic_output(destination) as temporary:
        temporary.write_text("complete\n", encoding="utf-8")

    assert descriptor_is_writable == [True]
    assert destination.read_text(encoding="utf-8") == "complete\n"


def test_atomic_output_cleans_temporary_file_after_failure(tmp_path: Path) -> None:
    store = LocalWorkspaceStore(tmp_path)
    workspace_id = store.create_workspace()
    destination = store.export_path(
        workspace_id=workspace_id,
        result_id="result-001",
        filename="table.csv",
    )

    with pytest.raises(RuntimeError), store.atomic_output(destination) as temporary:
        temporary.write_text("partial\n", encoding="utf-8")
        raise RuntimeError("stop")

    assert not destination.exists()
    assert not list(destination.parent.glob("*.tmp*"))


def test_delete_waits_for_cross_process_result_access(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys
    from time import monotonic, sleep

    store = LocalWorkspaceStore(tmp_path, lock_timeout_seconds=5)
    workspace_id = store.create_workspace()
    store.write_result_bytes(
        workspace_id=workspace_id,
        result_id="result-001",
        payload=b"result",
    )
    started = tmp_path / "child-started"
    completed = tmp_path / "child-completed"
    code = """
import sys
from pathlib import Path
from quantas_gui.services.workspaces import LocalWorkspaceStore

root = Path(sys.argv[1])
workspace_id = sys.argv[2]
started = Path(sys.argv[3])
completed = Path(sys.argv[4])
started.write_text("started", encoding="utf-8")
LocalWorkspaceStore(root, lock_timeout_seconds=5).delete_workspace(workspace_id)
completed.write_text("completed", encoding="utf-8")
"""

    process: subprocess.Popen[str] | None = None
    try:
        with store.result_access(workspace_id=workspace_id, result_id="result-001") as path:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    code,
                    str(tmp_path),
                    workspace_id,
                    str(started),
                    str(completed),
                ],
                env=os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = monotonic() + 5
            while not started.exists() and monotonic() < deadline:
                sleep(0.01)
            assert started.exists(), "the child process did not start"
            sleep(0.1)
            assert process.poll() is None
            assert path.is_file()
            assert not completed.exists()

        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, f"stdout={stdout!r} stderr={stderr!r}"
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate(timeout=5)

    assert completed.exists()
    assert not store.workspace_path(workspace_id).exists()


def test_new_result_access_is_rejected_after_deletion_begins(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from time import monotonic, sleep

    store = LocalWorkspaceStore(tmp_path, lock_timeout_seconds=2)
    workspace_id = store.create_workspace()
    store.write_result_bytes(
        workspace_id=workspace_id,
        result_id="result-001",
        payload=b"result",
    )
    workspace = store.workspace_path(workspace_id)

    def delete() -> None:
        store.delete_workspace(workspace_id)

    def read_again() -> None:
        with store.result_access(workspace_id=workspace_id, result_id="result-001"):
            raise AssertionError("a closing workspace must not admit a new reader")

    with ThreadPoolExecutor(max_workers=2) as executor:
        with store.result_access(workspace_id=workspace_id, result_id="result-001"):
            deletion = executor.submit(delete)
            deadline = monotonic() + 2
            while not (workspace / ".closing").exists() and monotonic() < deadline:
                sleep(0.01)
            assert (workspace / ".closing").exists()
            reader = executor.submit(read_again)
        with pytest.raises(FileNotFoundError):
            reader.result(timeout=3)
        assert deletion.result(timeout=3) is None

    assert not workspace.exists()
