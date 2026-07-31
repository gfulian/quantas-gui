from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("dash")
pytest.importorskip("dash_ag_grid")

from dash._utils import to_json

from quantas_gui.app import create_app
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.config import Settings
from quantas_gui.forms.renderer import render_form
from quantas_gui.pages.elasticity import layout
from quantas_gui.services.backend_info import detect_quantas_backend
from quantas_gui.services.backends import (
    ExecutionBackendDescriptor,
    JobState,
    JobStatus,
)
from quantas_gui.workflows.elasticity.callbacks import _is_elasticity_result_handoff
from quantas_gui.workflows.elasticity.ids import ElasticityIds
from quantas_gui.workflows.elasticity.presentation import failed_view
from quantas_gui.workflows.elasticity.schema import elasticity_form


def test_elasticity_form_and_page_serialize_with_required_workflow_controls() -> None:
    compatibility = detect_quantas_backend()
    if not compatibility.workflow_ready("elasticity"):
        pytest.skip("compatible Quantas Elasticity lifecycle is unavailable")

    schema = elasticity_form()
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
    assert "GPa" in form_payload
    assert "density" not in form_payload.lower()
    assert "density" not in {field.key for field in schema.fields}
    assert "crystal_symmetry" not in {field.key for field in schema.fields}
    assert "infers crystal symmetry" in form_payload.lower()
    for component_id in (
        ElasticityIds.SESSION,
        ElasticityIds.EVENTS,
        ElasticityIds.POLL,
        ElasticityIds.RUNTIME,
        ElasticityIds.ACTIVITY,
        ElasticityIds.SUMMARY,
    ):
        assert component_id in page_payload


def test_failure_and_cancelled_states_are_visually_distinct() -> None:
    failed = to_json(
        failed_view(
            JobStatus(
                state=JobState.FAILED,
                message="Worker failed",
                error="The calculation process terminated unexpectedly.",
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


def test_standard_app_registers_elasticity_workflow_callbacks(tmp_path: Path) -> None:
    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    app = create_app(settings)
    callback_keys = "\n".join(app.callback_map)
    shell_payload = to_json(app.layout())

    assert '"id":"q-location"' in shell_payload
    assert '"refresh":"callback-nav"' in shell_payload
    assert "q-location.href" in callback_keys
    navigation_callback = app.callback_map["q-location.href"]
    assert {"id": ResultIds.SESSION, "property": "modified_timestamp"} in navigation_callback[
        "inputs"
    ]
    result_shell_callback = next(
        callback
        for output, callback in app.callback_map.items()
        if ResultIds.UPLOAD_PANEL in output
        and ResultIds.WORKSPACE in output
        and ResultIds.HEADER in output
    )
    assert {"id": "q-location", "property": "pathname"} in result_shell_callback["inputs"]
    assert {
        "id": ResultIds.HYDRATE,
        "property": "n_intervals",
        "allow_optional": True,
    } in result_shell_callback["inputs"]
    result_tab_callback = app.callback_map[f"{ResultIds.TAB_CONTENT}.children"]
    assert {
        "id": ResultIds.HYDRATE,
        "property": "n_intervals",
        "allow_optional": True,
    } in result_tab_callback["inputs"]
    assert ElasticityIds.SESSION in callback_keys
    assert ElasticityIds.EVENTS in callback_keys
    assert ElasticityIds.DOWNLOAD_HDF5_PAYLOAD in callback_keys
    assert ElasticityIds.DOWNLOAD_REPORT_PAYLOAD in callback_keys
    assert ElasticityIds.DOWNLOAD_DIAGNOSTIC_PAYLOAD in callback_keys


def test_result_handoff_waits_for_the_global_session_before_navigation() -> None:
    active_result = {
        "reference": {
            "workspace_id": "workspace",
            "result_id": "result",
            "filename": "elasticity.hdf5",
            "size_bytes": 1024,
            "disposable_workspace": False,
        },
        "summary": {
            "module": "elasticity",
            "module_title": "Elasticity",
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

    assert _is_elasticity_result_handoff(
        result_session=active_result,
        workflow_session=workflow_session,
        pathname="/elasticity",
    )
    assert not _is_elasticity_result_handoff(
        result_session=active_result,
        workflow_session=workflow_session,
        pathname="/results",
    )
    assert not _is_elasticity_result_handoff(
        result_session={**active_result, "summary": {**active_result["summary"], "event_count": 1}},
        workflow_session=workflow_session,
        pathname="/elasticity",
    )
