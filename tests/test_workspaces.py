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
