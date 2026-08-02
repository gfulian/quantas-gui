from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("dash")
pytest.importorskip("dash_ag_grid")

from dash._utils import to_json

from quantas_gui.app import create_app
from quantas_gui.config import Settings
from quantas_gui.forms.renderer import render_form
from quantas_gui.pages.seismic import layout
from quantas_gui.services.backend_info import detect_quantas_backend
from quantas_gui.services.backends import ExecutionBackendDescriptor, JobState, JobStatus
from quantas_gui.workflows.seismic.callbacks import _is_seismic_result_handoff
from quantas_gui.workflows.seismic.ids import SeismicIds
from quantas_gui.workflows.seismic.presentation import failed_view
from quantas_gui.workflows.seismic.schema import seismic_form


def test_seismic_form_and_page_serialize_with_required_workflow_controls() -> None:
    compatibility = detect_quantas_backend()
    if not compatibility.workflow_ready("seismic"):
        pytest.skip("compatible Quantas SEISMIC lifecycle is unavailable")

    schema = seismic_form()
    form_payload = to_json(render_form(schema))
    page_payload = to_json(
        layout(
            backend=compatibility,
            execution=ExecutionBackendDescriptor(
                kind="local-process",
                available=True,
                process_shared=False,
                supports_cancellation=True,
                detail="Separate local process.",
            ),
        )
    )

    assert "Elastic stiffness matrix" in form_payload
    assert "Density" in form_payload
    assert "kg m" in form_payload
    assert "Phase velocity" in form_payload
    assert "Enhancement" in form_payload
    assert "batch_size" not in {field.key for field in schema.fields}
    assert "crystal_symmetry" not in {field.key for field in schema.fields}
    for component_id in (
        SeismicIds.SESSION,
        SeismicIds.EVENTS,
        SeismicIds.POLL,
        SeismicIds.RUNTIME,
        SeismicIds.ACTIVITY,
        SeismicIds.SUMMARY,
        SeismicIds.DOWNLOAD_CSV_PAYLOAD,
    ):
        assert component_id in page_payload


def test_seismic_failure_and_cancelled_states_are_visually_distinct() -> None:
    failed = to_json(
        failed_view(
            JobStatus(
                state=JobState.FAILED,
                message="Worker failed",
                error="Seismic propagation requires a positive-definite stiffness matrix.",
            )
        )
    )
    cancelled = to_json(
        failed_view(
            JobStatus(state=JobState.CANCELLED, message="Cancelled"),
            cancelled=True,
        )
    )

    assert "Calculation failed" in failed
    assert "No valid HDF5 result was published" in failed
    assert "Calculation cancelled" in cancelled
    assert "No result was published" in cancelled


def test_standard_app_registers_seismic_workflow_callbacks(tmp_path: Path) -> None:
    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    app = create_app(settings)
    callback_keys = "\n".join(app.callback_map)

    assert SeismicIds.SESSION in callback_keys
    assert SeismicIds.EVENTS in callback_keys
    assert SeismicIds.DOWNLOAD_HDF5_PAYLOAD in callback_keys
    assert SeismicIds.DOWNLOAD_REPORT_PAYLOAD in callback_keys
    assert SeismicIds.DOWNLOAD_CSV_PAYLOAD in callback_keys
    assert SeismicIds.DOWNLOAD_DIAGNOSTIC_PAYLOAD in callback_keys
    assert any("q-location.href" in key for key in app.callback_map)


def test_seismic_result_handoff_waits_for_global_session() -> None:
    active_result = {
        "reference": {
            "workspace_id": "workspace",
            "result_id": "result",
            "filename": "seismic.hdf5",
            "size_bytes": 1024,
            "disposable_workspace": False,
        },
        "summary": {
            "module": "seismic",
            "module_title": "SEISMIC",
            "method": None,
            "program": None,
            "quantas_version": "2.0.0b7",
            "schema_version": "1",
            "created_at": None,
            "created_by": None,
            "capabilities": [],
            "warning_count": 0,
            "event_count": 0,
            "result_keys": [],
            "archive": False,
        },
    }
    workflow_session = {"active_result": active_result}

    assert _is_seismic_result_handoff(
        result_session=active_result,
        workflow_session=workflow_session,
        pathname="/seismic",
    )
    assert not _is_seismic_result_handoff(
        result_session=active_result,
        workflow_session=workflow_session,
        pathname="/results",
    )
    assert not _is_seismic_result_handoff(
        result_session={**active_result, "summary": {**active_result["summary"], "event_count": 1}},
        workflow_session=workflow_session,
        pathname="/seismic",
    )
