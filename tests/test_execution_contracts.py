from __future__ import annotations

import pytest

from quantas_gui.services.backends import JobEvent, JobHandle, JobState, JobStatus


def test_job_handle_round_trip_validates_opaque_identifiers() -> None:
    handle = JobHandle(job_id="job-001", workspace_id="workspace_001")
    assert JobHandle.from_dict(handle.as_dict()) == handle
    with pytest.raises(ValueError, match="invalid job_id"):
        JobHandle(job_id="../escape", workspace_id="workspace")


def test_job_event_round_trip_preserves_cursor_and_payload() -> None:
    event = JobEvent(
        sequence=3,
        created_at=123.5,
        level="progress",
        message="Sampling directions",
        progress=0.25,
        data={"current": 25, "total": 100},
    )
    assert JobEvent.from_dict(event.as_dict()) == event


def test_job_status_round_trip_preserves_terminal_result() -> None:
    status = JobStatus(
        state=JobState.SUCCEEDED,
        progress=1.0,
        message="Complete",
        result_id="result-001",
        submitted_at=1.0,
        started_at=2.0,
        updated_at=3.0,
        finished_at=3.0,
        next_event_sequence=4,
    )
    assert JobStatus.from_dict(status.as_dict()) == status


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_job_progress_is_bounded(value: float) -> None:
    with pytest.raises(ValueError, match="progress must be between 0 and 1"):
        JobStatus(state=JobState.RUNNING, progress=value)


def test_job_status_rejects_string_boolean() -> None:
    with pytest.raises(ValueError, match="expected a boolean"):
        JobStatus.from_dict({"state": "queued", "cancel_requested": "false"})


def test_job_status_accepts_numeric_timestamp_strings() -> None:
    status = JobStatus.from_dict(
        {
            "state": "running",
            "submitted_at": "1.25",
            "started_at": 2,
        }
    )

    assert status.submitted_at == 1.25
    assert status.started_at == 2.0


@pytest.mark.parametrize("value", [False, object(), {"seconds": 1}])
def test_job_status_rejects_non_numeric_timestamps(value: object) -> None:
    with pytest.raises(ValueError, match="expected a number"):
        JobStatus.from_dict({"state": "queued", "submitted_at": value})
