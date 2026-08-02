from __future__ import annotations

import time
from pathlib import Path

import h5py
import numpy as np
import pytest

from quantas_gui.services.backend_info import detect_quantas_backend
from quantas_gui.services.backends import JobState
from quantas_gui.services.cache import LocalArtifactCache
from quantas_gui.services.local_execution import LocalProcessExecutionBackend
from quantas_gui.services.result_backend import QuantasResultBackend
from quantas_gui.services.results import ResultExplorerService
from quantas_gui.services.workspaces import LocalWorkspaceStore
from quantas_gui.workflows.common import RotationRequest
from quantas_gui.workflows.seismic.adapter import build_public_contracts
from quantas_gui.workflows.seismic.request import SeismicRequest
from quantas_gui.workflows.seismic.service import SeismicWorkflowService


def _stiffness() -> tuple[tuple[float, ...], ...]:
    return (
        (220.0, 80.0, 70.0, 0.0, 0.0, 0.0),
        (80.0, 190.0, 65.0, 0.0, 0.0, 0.0),
        (70.0, 65.0, 250.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 75.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 68.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 60.0),
    )


def _wait(service: SeismicWorkflowService, handle, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = service.status(handle)
        if status.state in {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}:
            return status
        time.sleep(0.05)
    raise AssertionError(f"SEISMIC job did not finish: {service.status(handle)}")


def test_request_round_trip_preserves_scientific_options() -> None:
    request = SeismicRequest(
        jobname="Reference",
        stiffness=_stiffness(),
        density=3178.0,
        ntheta=5,
        nphi=9,
        hemisphere="full",
        level="group",
        batch_size=7,
        track_polarization_axes=False,
        rotation=RotationRequest(kind="xyz", values=(10.0, 20.0, 30.0)),
    )

    assert SeismicRequest.from_dict(request.as_dict()) == request


def test_request_requires_density_for_manual_input() -> None:
    with pytest.raises(ValueError, match="stiffness and density"):
        SeismicRequest(jobname="Missing density", stiffness=_stiffness())
    with pytest.raises(ValueError, match="finite and positive"):
        SeismicRequest(jobname="Bad density", stiffness=_stiffness(), density=0.0)


def test_adapter_constructs_only_public_seismic_contracts(tmp_path: Path) -> None:
    request = SeismicRequest(
        jobname="Rotated",
        stiffness=_stiffness(),
        density=3178.0,
        ntheta=5,
        nphi=9,
        hemisphere="lower",
        level="enhancement",
        batch_size=8,
        track_polarization_axes=True,
        rotation=RotationRequest(kind="xyz", values=(0.0, 0.0, 30.0)),
    )
    input_data, options = build_public_contracts(request, workspace_path=tmp_path)

    assert input_data.jobname == "Rotated"
    assert input_data.stiffness is not None
    assert input_data.density == pytest.approx(3178.0)
    assert options.ntheta == 5
    assert options.nphi == 9
    assert options.hemisphere.value == "lower"
    assert options.level.value == "enhancement"
    assert options.batch_size == 8
    assert options.track_polarization_axes is True
    assert options.rotation is not None


def test_process_workflow_matches_direct_public_api_and_hands_off_result(
    tmp_path: Path,
) -> None:
    from quantas.api import seismic

    compatibility = detect_quantas_backend()
    if not compatibility.workflow_ready("seismic"):
        pytest.skip("compatible Quantas SEISMIC API is unavailable")

    store = LocalWorkspaceStore(tmp_path / "workspaces", lock_timeout_seconds=10.0)
    execution = LocalProcessExecutionBackend(store)
    results = ResultExplorerService(
        workspace_store=store,
        backend=QuantasResultBackend(),
        max_upload_bytes=16 * 1024 * 1024,
        compatibility=compatibility,
        cache=LocalArtifactCache(max_entries=8),
    )
    service = SeismicWorkflowService(store, execution, results)
    request = SeismicRequest(
        jobname="API equivalence",
        stiffness=_stiffness(),
        density=3178.0,
        ntheta=5,
        nphi=9,
        hemisphere="upper",
        level="enhancement",
        batch_size=7,
        track_polarization_axes=True,
        rotation=RotationRequest(kind="xyz", values=(10.0, 20.0, 30.0)),
    )

    direct_input, direct_options = build_public_contracts(request, workspace_path=tmp_path)
    direct = seismic.run(direct_input, direct_options)
    handle = service.submit(request)
    status = _wait(service, handle)

    assert status.state is JobState.SUCCEEDED, status.error
    events = service.events(handle)
    forbidden_event_keys = {"input", "result", "options", "velocities", "diagnostics"}
    assert all(forbidden_event_keys.isdisjoint(event.data) for event in events)
    progress_events = [
        event
        for event in events
        if isinstance(event.data.get("current"), int) and isinstance(event.data.get("total"), int)
    ]
    assert len(progress_events) >= 2
    visible_progress = [event.progress for event in events if event.progress is not None]
    assert visible_progress == sorted(visible_progress)

    assert status.result_id is not None
    result_path = store.result_path(
        workspace_id=handle.workspace_id,
        result_id=status.result_id,
    )
    with h5py.File(result_path, "r") as h5:
        report_text = h5["diagnostics/report_text"][()]
        if isinstance(report_text, bytes):
            report_text = report_text.decode("utf-8")
        assert "Seismic calculation summary" in str(report_text)
        assert "Sampled phase-velocity extrema" in str(report_text)

    restored = seismic.read_result(result_path)
    direct_payload = seismic.get_result(direct)
    restored_payload = seismic.get_result(restored)
    assert restored_payload.density == pytest.approx(direct_payload.density)
    np.testing.assert_allclose(restored_payload.stiffness, direct_payload.stiffness, rtol=0, atol=0)
    np.testing.assert_allclose(
        restored_payload.averages.as_array(),
        direct_payload.averages.as_array(),
        rtol=1.0e-14,
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        restored_payload.isotropic_velocities.as_array(),
        direct_payload.isotropic_velocities.as_array(),
        rtol=1.0e-14,
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        restored_payload.field.phase.phase_speeds,
        direct_payload.field.phase.phase_speeds,
        rtol=1.0e-12,
        atol=1.0e-12,
        equal_nan=True,
    )
    assert restored_payload.field.group is not None
    assert direct_payload.field.group is not None
    np.testing.assert_allclose(
        restored_payload.field.group.group_speeds,
        direct_payload.field.group.group_speeds,
        rtol=1.0e-12,
        atol=1.0e-12,
        equal_nan=True,
    )
    assert restored_payload.field.enhancement is not None
    assert direct_payload.field.enhancement is not None
    np.testing.assert_allclose(
        restored_payload.field.enhancement.log10_enhancement,
        direct_payload.field.enhancement.log10_enhancement,
        rtol=1.0e-12,
        atol=1.0e-12,
        equal_nan=True,
    )

    active = service.active_result(handle, jobname=request.jobname)
    opened = results.open_reference(active.reference)
    assert opened.summary.module == "seismic"

    csv_path = service.sampled_csv(active)
    assert csv_path.is_file()
    csv_text = csv_path.read_text(encoding="utf-8")
    assert "phase" in csv_text.lower()
    assert service.sampled_csv(active) == csv_path


def test_unstable_stiffness_fails_without_publishing_result(tmp_path: Path) -> None:
    compatibility = detect_quantas_backend()
    if not compatibility.workflow_ready("seismic"):
        pytest.skip("compatible Quantas SEISMIC API is unavailable")
    store = LocalWorkspaceStore(tmp_path / "workspaces", lock_timeout_seconds=10.0)
    execution = LocalProcessExecutionBackend(store)
    results = ResultExplorerService(
        workspace_store=store,
        backend=QuantasResultBackend(),
        max_upload_bytes=16 * 1024 * 1024,
        compatibility=compatibility,
        cache=LocalArtifactCache(max_entries=4),
    )
    service = SeismicWorkflowService(store, execution, results)
    unstable = [list(row) for row in _stiffness()]
    unstable[3][3] = -1.0
    request = SeismicRequest(
        jobname="Unstable",
        stiffness=tuple(tuple(row) for row in unstable),
        density=3178.0,
        ntheta=3,
        nphi=5,
        level="phase",
    )

    handle = service.submit(request)
    status = _wait(service, handle)

    assert status.state is JobState.FAILED
    assert status.result_id is None
    assert status.error is not None
    assert "positive-definite" in status.error
    assert not list((store.workspace_path(handle.workspace_id) / "results").iterdir())
