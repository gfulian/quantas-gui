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
from quantas_gui.workflows.elasticity.adapter import build_public_contracts
from quantas_gui.workflows.elasticity.request import ElasticityRequest, RotationRequest
from quantas_gui.workflows.elasticity.schema import build_request, elasticity_form
from quantas_gui.workflows.elasticity.service import ElasticityWorkflowService


def _stiffness() -> tuple[tuple[float, ...], ...]:
    return (
        (220.0, 80.0, 70.0, 0.0, 0.0, 0.0),
        (80.0, 190.0, 65.0, 0.0, 0.0, 0.0),
        (70.0, 65.0, 250.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 75.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 68.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 60.0),
    )


def _wait(service: ElasticityWorkflowService, handle, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = service.status(handle)
        if status.state in {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}:
            return status
        time.sleep(0.05)
    raise AssertionError(f"Elasticity job did not finish: {service.status(handle)}")


def test_request_excludes_density_and_manual_symmetry() -> None:
    request = ElasticityRequest(jobname="Reference", stiffness=_stiffness())
    value = request.as_dict()

    assert "density" not in value
    assert "symmetry" not in value
    assert ElasticityRequest.from_dict(value) == request


def test_rotation_request_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="rotation kind"):
        RotationRequest(kind="invalid", values=(1.0,) * 9)  # type: ignore[arg-type]


def test_request_defers_stiffness_symmetry_tolerance_to_quantas(tmp_path: Path) -> None:
    from quantas.api import elasticity

    matrix = [list(row) for row in _stiffness()]
    matrix[0][1] = 99.0
    request = ElasticityRequest(
        jobname="Backend validation",
        stiffness=tuple(tuple(row) for row in matrix),
    )
    input_data, options = build_public_contracts(request, workspace_path=tmp_path)

    assert input_data.stiffness is not None
    assert input_data.stiffness[0, 1] == 99.0
    with pytest.raises(ValueError, match="symmetric"):
        elasticity.run(input_data, options)


def test_compact_triangle_reaches_the_public_api_as_a_symmetric_tensor(
    tmp_path: Path,
) -> None:
    from quantas.api import elasticity

    values = {field.key: field.default for field in elasticity_form().fields}
    values["jobname"] = "Compact upper triangle"
    values["stiffness_text"] = """220 80 70 0 0 0
190 65 0 0 0
250 0 0 0
75 0 0
68 0
60"""
    checked = build_request(values)

    assert checked.valid
    assert checked.request is not None
    input_data, options = build_public_contracts(checked.request, workspace_path=tmp_path)
    result = elasticity.run(input_data, options)
    payload = elasticity.get_result(result)

    np.testing.assert_allclose(payload.stiffness, np.asarray(_stiffness()), rtol=0, atol=0)


def test_adapter_constructs_only_public_elasticity_contracts(tmp_path: Path) -> None:
    request = ElasticityRequest(
        jobname="Rotated",
        stiffness=_stiffness(),
        calculate_2d=True,
        ntheta_2d=19,
        calculate_3d=True,
        ntheta_3d=7,
        nphi_3d=11,
        properties_3d=("young", "shear"),
        rotation=RotationRequest(kind="xyz", values=(0.0, 0.0, 30.0)),
    )
    input_data, options = build_public_contracts(request, workspace_path=tmp_path)

    assert input_data.jobname == "Rotated"
    assert input_data.stiffness is not None
    assert not hasattr(input_data, "density")
    assert options.calculate_2d is True
    assert options.ntheta == 19
    assert options.calculate_3d is True
    assert options.surface_options is not None
    assert options.surface_options.ntheta == 7
    assert options.surface_options.nphi == 11
    assert options.surface_options.properties == ("young", "shear")
    assert options.rotation is not None


def test_process_workflow_matches_direct_public_api_and_hands_off_result(
    tmp_path: Path,
) -> None:
    from quantas.api import elasticity

    compatibility = detect_quantas_backend()
    if not compatibility.workflow_ready("elasticity"):
        pytest.skip("compatible Quantas Elasticity API is unavailable")

    store = LocalWorkspaceStore(tmp_path / "workspaces", lock_timeout_seconds=10.0)
    execution = LocalProcessExecutionBackend(store)
    results = ResultExplorerService(
        workspace_store=store,
        backend=QuantasResultBackend(),
        max_upload_bytes=16 * 1024 * 1024,
        compatibility=compatibility,
        cache=LocalArtifactCache(max_entries=8),
    )
    service = ElasticityWorkflowService(store, execution, results)
    request = ElasticityRequest(
        jobname="API equivalence",
        stiffness=_stiffness(),
        calculate_2d=True,
        ntheta_2d=9,
        calculate_3d=True,
        ntheta_3d=5,
        nphi_3d=7,
        properties_3d=("young",),
        batch_size=32,
        rotation=RotationRequest(kind="xyz", values=(10.0, 20.0, 30.0)),
    )

    direct_input, direct_options = build_public_contracts(request, workspace_path=tmp_path)
    direct = elasticity.run(direct_input, direct_options)
    handle = service.submit(request)
    status = _wait(service, handle)

    assert status.state is JobState.SUCCEEDED, status.error
    events = service.events(handle)
    forbidden_event_keys = {"input", "result", "options", "source_stiffness", "analysis_stiffness"}
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
        assert "Voigt-Reuss-Hill average properties" in str(report_text)
        assert "Mechanical stability" in str(report_text)

    restored = elasticity.read_result(result_path)
    direct_payload = elasticity.get_result(direct)
    restored_payload = elasticity.get_result(restored)
    np.testing.assert_allclose(restored_payload.stiffness, direct_payload.stiffness, rtol=0, atol=0)
    np.testing.assert_allclose(
        restored_payload.compliance,
        direct_payload.compliance,
        rtol=1.0e-14,
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        restored_payload.averages.as_array(),
        direct_payload.averages.as_array(),
        rtol=1.0e-14,
        atol=1.0e-14,
    )
    assert restored_payload.crystal_system == direct_payload.crystal_system
    assert restored_payload.stability.is_stable is direct_payload.stability.is_stable

    assert restored_payload.variations.keys() == direct_payload.variations.keys()
    for key, direct_variation in direct_payload.variations.items():
        restored_variation = restored_payload.variations[key]
        np.testing.assert_allclose(
            (
                restored_variation.minimum,
                restored_variation.maximum,
                restored_variation.anisotropy,
            ),
            (
                direct_variation.minimum,
                direct_variation.maximum,
                direct_variation.anisotropy,
            ),
            rtol=1.0e-12,
            atol=1.0e-12,
        )
        np.testing.assert_allclose(
            restored_variation.minimum_axis,
            direct_variation.minimum_axis,
            rtol=1.0e-12,
            atol=1.0e-12,
        )
        np.testing.assert_allclose(
            restored_variation.maximum_axis,
            direct_variation.maximum_axis,
            rtol=1.0e-12,
            atol=1.0e-12,
        )

    assert restored_payload.properties_2d.keys() == direct_payload.properties_2d.keys()
    for plane, direct_plane in direct_payload.properties_2d.items():
        restored_plane = restored_payload.properties_2d[plane]
        assert restored_plane.keys() == direct_plane.keys()
        for key, direct_values in direct_plane.items():
            np.testing.assert_allclose(
                restored_plane[key],
                direct_values,
                rtol=1.0e-12,
                atol=1.0e-12,
            )

    assert restored_payload.properties_3d is not None
    assert direct_payload.properties_3d is not None
    assert (
        restored_payload.properties_3d.surfaces.keys()
        == direct_payload.properties_3d.surfaces.keys()
    )
    for key, direct_surface in direct_payload.properties_3d.surfaces.items():
        restored_surface = restored_payload.properties_3d.surfaces[key]
        assert restored_surface.unit == direct_surface.unit
        for attribute in ("theta", "phi", "radius", "values", "x", "y", "z"):
            np.testing.assert_allclose(
                getattr(restored_surface, attribute),
                getattr(direct_surface, attribute),
                rtol=1.0e-12,
                atol=1.0e-12,
            )

    active = service.active_result(handle, jobname=request.jobname)
    assert active.reference.disposable_workspace is False
    assert active.reference.workspace_id == handle.workspace_id
    assert active.summary.module == "elasticity"


def test_mechanically_unstable_tensor_succeeds_with_warning_and_no_directional_data(
    tmp_path: Path,
) -> None:
    from quantas.api import elasticity

    compatibility = detect_quantas_backend()
    if not compatibility.workflow_ready("elasticity"):
        pytest.skip("compatible Quantas Elasticity API is unavailable")

    matrix = [list(row) for row in _stiffness()]
    matrix[3][3] = -1.0
    store = LocalWorkspaceStore(tmp_path / "workspaces", lock_timeout_seconds=10.0)
    execution = LocalProcessExecutionBackend(store)
    results = ResultExplorerService(
        workspace_store=store,
        backend=QuantasResultBackend(),
        max_upload_bytes=16 * 1024 * 1024,
        compatibility=compatibility,
        cache=LocalArtifactCache(max_entries=8),
    )
    service = ElasticityWorkflowService(store, execution, results)
    request = ElasticityRequest(
        jobname="Unstable tensor",
        stiffness=tuple(tuple(row) for row in matrix),
        calculate_2d=True,
        ntheta_2d=19,
        calculate_3d=True,
        ntheta_3d=7,
        nphi_3d=13,
    )

    handle = service.submit(request)
    status = _wait(service, handle)

    assert status.state is JobState.SUCCEEDED, status.error
    assert status.result_id is not None
    events = service.events(handle)
    assert any(event.level == "warning" for event in events)
    result = elasticity.read_result(
        store.result_path(
            workspace_id=handle.workspace_id,
            result_id=status.result_id,
        )
    )
    payload = elasticity.get_result(result)
    assert payload.stability.is_stable is False
    assert payload.properties_2d == {}
    assert payload.properties_3d is None
    active = service.active_result(handle, jobname=request.jobname)
    assert active.summary.warning_count >= 1
