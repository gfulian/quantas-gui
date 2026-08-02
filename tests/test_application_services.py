from __future__ import annotations

from pathlib import Path

from quantas_gui.config import Settings
from quantas_gui.services.application import build_default_services
from quantas_gui.services.backend_info import REQUIRED_QUANTAS, BackendCompatibility
from quantas_gui.services.local_execution import LocalProcessExecutionBackend


def test_local_execution_is_available_when_seismic_is_the_only_ready_workflow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    compatibility = BackendCompatibility(
        available=True,
        compatible=True,
        version="2.0.0b8",
        required_version=REQUIRED_QUANTAS,
        missing_capabilities=(),
        detail="ready",
        workflow_missing=(("elasticity", ("run",)),),
    )
    monkeypatch.setattr(
        "quantas_gui.services.application.detect_quantas_backend",
        lambda: compatibility,
    )
    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )

    services = build_default_services(settings)

    assert compatibility.workflow_ready("elasticity") is False
    assert compatibility.workflow_ready("seismic") is True
    assert isinstance(services.execution, LocalProcessExecutionBackend)
