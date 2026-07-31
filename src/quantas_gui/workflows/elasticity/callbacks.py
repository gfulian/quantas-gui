"""Dash callbacks for the executable Elasticity workflow."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from contextlib import suppress
from typing import Any

import dash
from dash import Input, Output, State, ctx, dcc, no_update

from quantas_gui.components.feedback import message_banner, validation_summary
from quantas_gui.components.result_ids import ResultIds
from quantas_gui.forms.ids import FormIds
from quantas_gui.forms.schema import (
    BooleanField,
    ChoiceField,
    FieldKind,
    FileUploadField,
    MatrixField,
    RangeTripletField,
    TagsField,
    VectorField,
)
from quantas_gui.forms.validation import field_is_visible
from quantas_gui.forms.values import (
    matrix_to_row_data,
    normalize_component_value,
    value_component_id,
    value_property,
)
from quantas_gui.models import ActiveResultState
from quantas_gui.services.backends import JobHandle, JobState, JobStatus
from quantas_gui.services.public_errors import public_error_message
from quantas_gui.workflows.elasticity.ids import ElasticityIds
from quantas_gui.workflows.elasticity.presentation import (
    active_job_view,
    activity_view,
    diagnostic_text,
    failed_view,
    queued_view,
    success_view,
)
from quantas_gui.workflows.elasticity.schema import (
    build_request,
    elasticity_form,
    format_stiffness,
    input_mode,
)
from quantas_gui.workflows.elasticity.service import ElasticityWorkflowService

_LOGGER = logging.getLogger(__name__)
_SCHEMA = elasticity_form()
_FIELDS = tuple(field for field in _SCHEMA.fields if not isinstance(field, FileUploadField))
_UPLOAD = _SCHEMA.field("source_upload")
_VALUE_STATES = tuple(
    State(value_component_id(_SCHEMA.key, field), value_property(field)) for field in _FIELDS
)
_ERROR_OUTPUTS = tuple(
    Output(FormIds.error(_SCHEMA.key, field.key), "children") for field in _FIELDS
)
_RESET_OUTPUTS = tuple(
    Output(value_component_id(_SCHEMA.key, field), value_property(field)) for field in _FIELDS
)
_CONDITIONAL_FIELDS = tuple(field for field in _SCHEMA.fields if field.visible_when)

_FORM_VISIBLE = "q-workflow-form-host"
_FORM_HIDDEN = "q-workflow-form-host is-hidden"
_RUNTIME_VISIBLE = "q-workflow-runtime"
_RUNTIME_HIDDEN = "q-workflow-runtime is-hidden"
_ACTIVITY_VISIBLE = "q-workflow-activity"
_ACTIVITY_HIDDEN = "q-workflow-activity is-hidden"
_SUMMARY_VISIBLE = "q-workflow-summary"
_SUMMARY_HIDDEN = "q-workflow-summary is-hidden"
_MAX_BROWSER_EVENTS = 500


def register_elasticity_callbacks(
    app: dash.Dash,
    service: ElasticityWorkflowService,
) -> None:
    """Register input, execution, activity, handoff, and download callbacks."""
    _register_input_callbacks(app, service)
    _register_visibility_callback(app)
    _register_orchestration_callback(app, service)
    _register_result_handoff_callback(app)
    _register_activity_callback(app)
    _register_download_callbacks(app, service)


def _register_input_callbacks(app: dash.Dash, service: ElasticityWorkflowService) -> None:
    @app.callback(
        *_RESET_OUTPUTS,
        Output(ElasticityIds.SOURCE, "data"),
        Output(ElasticityIds.IMPORT_STATUS, "children"),
        Input(
            {"type": "q-form-upload", "form": _SCHEMA.key, "field": _UPLOAD.key},
            "contents",
        ),
        Input(FormIds.reset(_SCHEMA.key), "n_clicks"),
        State(
            {"type": "q-form-upload", "form": _SCHEMA.key, "field": _UPLOAD.key},
            "filename",
        ),
        State(value_component_id(_SCHEMA.key, _SCHEMA.field("input_mode")), "value"),
        State(value_component_id(_SCHEMA.key, _SCHEMA.field("jobname")), "value"),
        State(ElasticityIds.SOURCE, "data"),
        State(ElasticityIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def import_or_reset(
        contents: str | None,
        reset_clicks: int | None,
        filename: str | None,
        raw_mode: object,
        jobname: object,
        source_state: Mapping[str, Any] | None,
        workflow_session: Mapping[str, Any] | None,
    ) -> tuple[Any, ...]:
        triggered = ctx.triggered_id
        if triggered == FormIds.reset(_SCHEMA.key):
            if (
                source_state
                and not workflow_session
                and bool(source_state.get("can_discard", False))
            ):
                with suppress(Exception):
                    service.discard_workspace(str(source_state.get("workspace_id", "")))
            return (*(_component_default(field) for field in _FIELDS), None, None)

        if not contents or not filename:
            return (*([no_update] * len(_FIELDS)), no_update, no_update)
        try:
            mode = input_mode(raw_mode)
            if mode == "manual":
                raise ValueError("Choose Quantas input, CRYSTAL output, or VASP OUTCAR first.")
            imported = service.import_upload(
                mode=mode,
                filename=filename,
                contents=contents,
                jobname=str(jobname or "Unknown"),
            )
        except Exception as exc:
            _LOGGER.warning("Elasticity source import rejected: %s", public_error_message(exc))
            return (
                *([no_update] * len(_FIELDS)),
                no_update,
                message_banner(
                    title="Input import failed",
                    message=public_error_message(exc),
                    level="error",
                ),
            )

        if source_state and not workflow_session and bool(source_state.get("can_discard", False)):
            with suppress(Exception):
                service.discard_workspace(str(source_state.get("workspace_id", "")))

        updates: list[Any] = [no_update] * len(_FIELDS)
        field_index = {field.key: index for index, field in enumerate(_FIELDS)}
        if imported.jobname is not None:
            updates[field_index["jobname"]] = imported.jobname
        updates[field_index["stiffness_text"]] = format_stiffness(imported.stiffness)
        source_payload = {
            "workspace_id": imported.workspace_id,
            "source_filename": imported.source_filename,
            "mode": mode,
            "display_filename": filename,
            "can_discard": True,
        }
        source_label = {
            "quantas": "Quantas input",
            "crystal": "CRYSTAL output",
            "vasp": "VASP OUTCAR",
        }[mode]
        return (
            *updates,
            source_payload,
            message_banner(
                title=f"{source_label} imported",
                message=(
                    "The editable stiffness matrix was populated through the public Quantas "
                    "Elasticity API."
                ),
                level="result",
            ),
        )


def _register_visibility_callback(app: dash.Dash) -> None:
    @app.callback(
        *(
            Output(FormIds.wrapper(_SCHEMA.key, field.key), "className")
            for field in _CONDITIONAL_FIELDS
        ),
        Input(value_component_id(_SCHEMA.key, _SCHEMA.field("input_mode")), "value"),
        Input(value_component_id(_SCHEMA.key, _SCHEMA.field("calculate_2d")), "value"),
        Input(value_component_id(_SCHEMA.key, _SCHEMA.field("calculate_3d")), "value"),
        Input(value_component_id(_SCHEMA.key, _SCHEMA.field("rotation_enabled")), "value"),
        Input(value_component_id(_SCHEMA.key, _SCHEMA.field("rotation_kind")), "value"),
    )
    def update_conditional_fields(
        raw_input_mode: object,
        raw_calculate_2d: object,
        raw_calculate_3d: object,
        raw_rotation_enabled: object,
        raw_rotation_kind: object,
    ) -> tuple[str, ...]:
        values = {
            "input_mode": raw_input_mode,
            "calculate_2d": bool(raw_calculate_2d),
            "calculate_3d": bool(raw_calculate_3d),
            "rotation_enabled": bool(raw_rotation_enabled),
            "rotation_kind": raw_rotation_kind,
        }
        return tuple(
            _field_class(field, visible=field_is_visible(field, values))
            for field in _CONDITIONAL_FIELDS
        )


def _register_orchestration_callback(
    app: dash.Dash,
    service: ElasticityWorkflowService,
) -> None:
    @app.callback(
        Output(ElasticityIds.SESSION, "data"),
        Output(ElasticityIds.SOURCE, "data", allow_duplicate=True),
        Output(ElasticityIds.EVENTS, "data"),
        Output(ElasticityIds.FORM_HOST, "className"),
        Output(ElasticityIds.RUNTIME, "className"),
        Output(ElasticityIds.RUNTIME, "children"),
        Output(ElasticityIds.ACTIVITY, "className"),
        Output(ElasticityIds.SUMMARY, "className"),
        Output(ElasticityIds.SUMMARY, "children"),
        Output(ElasticityIds.POLL, "disabled"),
        Output(FormIds.summary(_SCHEMA.key), "children"),
        *_ERROR_OUTPUTS,
        Output(ResultIds.SESSION, "data", allow_duplicate=True),
        Input(FormIds.submit(_SCHEMA.key), "n_clicks"),
        Input(ElasticityIds.POLL, "n_intervals"),
        Input(ElasticityIds.CANCEL, "n_clicks", allow_optional=True),
        Input(ElasticityIds.BACK, "n_clicks", allow_optional=True),
        Input(ElasticityIds.OPEN_RESULTS, "n_clicks", allow_optional=True),
        State(ElasticityIds.SESSION, "data"),
        State(ElasticityIds.SOURCE, "data"),
        State(ElasticityIds.EVENTS, "data"),
        *_VALUE_STATES,
        prevent_initial_call=True,
    )
    def orchestrate(
        submit_clicks: int | None,
        poll_count: int | None,
        cancel_clicks: int | None,
        back_clicks: int | None,
        open_clicks: int | None,
        workflow_session: Mapping[str, Any] | None,
        source_state: Mapping[str, Any] | None,
        stored_events: Sequence[Mapping[str, Any]] | None,
        *raw_values: Any,
    ) -> tuple[Any, ...]:
        del submit_clicks, poll_count, cancel_clicks, back_clicks, open_clicks
        triggered = ctx.triggered_id
        untouched_errors = [no_update] * len(_FIELDS)

        if triggered == ElasticityIds.OPEN_RESULTS:
            active_payload = None if not workflow_session else workflow_session.get("active_result")
            if not isinstance(active_payload, Mapping):
                return _orchestration_no_update(untouched_errors)
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                *untouched_errors,
                dict(active_payload),
            )

        if triggered == ElasticityIds.BACK:
            return (
                None,
                no_update,
                stored_events or [],
                _FORM_VISIBLE,
                _RUNTIME_HIDDEN,
                None,
                _ACTIVITY_HIDDEN,
                _SUMMARY_HIDDEN,
                None,
                True,
                None,
                *([""] * len(_FIELDS)),
                no_update,
            )

        if triggered == FormIds.submit(_SCHEMA.key):
            values = {
                field.key: normalize_component_value(field, raw)
                for field, raw in zip(_FIELDS, raw_values, strict=True)
            }
            selected_mode = input_mode(values.get("input_mode"))
            source_filename = None
            workspace_id = None
            source_matches_mode = bool(source_state and source_state.get("mode") == selected_mode)
            if source_matches_mode and source_state:
                raw_source = source_state.get("source_filename")
                raw_workspace = source_state.get("workspace_id")
                source_filename = None if raw_source is None else str(raw_source)
                workspace_id = None if raw_workspace is None else str(raw_workspace)
            checked = build_request(values, source_filename=source_filename)
            if not checked.valid or checked.request is None:
                errors = [
                    " ".join(issue.message for issue in checked.for_field(field.key))
                    for field in _FIELDS
                ]
                return (
                    no_update,
                    no_update,
                    no_update,
                    _FORM_VISIBLE,
                    _RUNTIME_HIDDEN,
                    None,
                    _ACTIVITY_HIDDEN,
                    _SUMMARY_HIDDEN,
                    None,
                    True,
                    validation_summary(checked.issues),
                    *errors,
                    no_update,
                )
            if (
                selected_mode == "manual"
                and source_state
                and bool(source_state.get("can_discard", False))
            ):
                with suppress(Exception):
                    service.discard_workspace(str(source_state.get("workspace_id", "")))
                source_state = None

            try:
                handle = service.submit(checked.request, workspace_id=workspace_id)
            except Exception as exc:
                _LOGGER.exception("Unable to submit the Elasticity job")
                return (
                    no_update,
                    no_update,
                    no_update,
                    _FORM_VISIBLE,
                    _RUNTIME_VISIBLE,
                    failed_view(
                        JobStatus(
                            state=JobState.FAILED,
                            message="Submission failed",
                            error=public_error_message(exc),
                        )
                    ),
                    _ACTIVITY_HIDDEN,
                    _SUMMARY_HIDDEN,
                    None,
                    True,
                    message_banner(
                        title="Calculation could not be submitted",
                        message=public_error_message(exc),
                        level="error",
                    ),
                    *([""] * len(_FIELDS)),
                    no_update,
                )
            session_payload = {
                "handle": handle.as_dict(),
                "jobname": checked.request.jobname,
                "cursor": 0,
                "status": JobStatus(
                    state=JobState.QUEUED,
                    progress=0.0,
                    message="Queued",
                ).as_dict(),
                "active_result": None,
            }
            updated_source = None if source_state is None else dict(source_state)
            if updated_source is not None:
                updated_source["can_discard"] = False
            return (
                session_payload,
                updated_source,
                [],
                _FORM_HIDDEN,
                _RUNTIME_VISIBLE,
                queued_view(),
                _ACTIVITY_VISIBLE,
                _SUMMARY_HIDDEN,
                None,
                False,
                None,
                *([""] * len(_FIELDS)),
                no_update,
            )

        if not workflow_session or "handle" not in workflow_session:
            return _orchestration_no_update(untouched_errors)
        try:
            handle = JobHandle.from_dict(dict(workflow_session["handle"]))
            if triggered == ElasticityIds.CANCEL:
                service.cancel(handle)
            status = service.status(handle)
            cursor = int(workflow_session.get("cursor", 0))
            new_events = tuple(service.events(handle, after_sequence=cursor, limit=200))
        except Exception as exc:
            _LOGGER.exception("Unable to poll the Elasticity job")
            status = JobStatus(
                state=JobState.FAILED,
                message="Status unavailable",
                error=public_error_message(exc),
            )
            new_events = ()

        events = [dict(item) for item in (stored_events or ())]
        events.extend(event.as_dict() for event in new_events)
        events = events[-_MAX_BROWSER_EVENTS:]
        next_cursor = max(
            (int(event.get("sequence", 0)) for event in events),
            default=int(workflow_session.get("cursor", 0)),
        )
        session_payload = dict(workflow_session)
        session_payload.update(cursor=next_cursor, status=status.as_dict())

        if status.state in {JobState.QUEUED, JobState.RUNNING, JobState.CANCELLING}:
            return (
                session_payload,
                no_update,
                events,
                _FORM_HIDDEN,
                _RUNTIME_VISIBLE,
                active_job_view(status, events),
                _ACTIVITY_VISIBLE,
                _SUMMARY_HIDDEN,
                None,
                False,
                no_update,
                *untouched_errors,
                no_update,
            )

        if status.state is JobState.SUCCEEDED:
            try:
                active = service.active_result(
                    handle,
                    jobname=str(workflow_session.get("jobname", "Elasticity")),
                )
                tables = service.results.build_tables(active.reference)
            except Exception as exc:
                _LOGGER.exception("Unable to prepare the Elasticity completion summary")
                failed_status = JobStatus(
                    state=JobState.FAILED,
                    message="Result handoff failed",
                    error=public_error_message(exc),
                )
                session_payload["status"] = failed_status.as_dict()
                return (
                    session_payload,
                    no_update,
                    events,
                    _FORM_HIDDEN,
                    _RUNTIME_VISIBLE,
                    failed_view(failed_status),
                    _ACTIVITY_VISIBLE,
                    _SUMMARY_HIDDEN,
                    None,
                    True,
                    no_update,
                    *untouched_errors,
                    no_update,
                )
            session_payload["active_result"] = active.as_dict()
            return (
                session_payload,
                no_update,
                events,
                _FORM_HIDDEN,
                _RUNTIME_HIDDEN,
                None,
                _ACTIVITY_VISIBLE,
                _SUMMARY_VISIBLE,
                success_view(
                    jobname=str(workflow_session.get("jobname", "Elasticity")),
                    warning_count=active.summary.warning_count,
                    events=events,
                    tables=tables,
                ),
                True,
                no_update,
                *untouched_errors,
                no_update,
            )

        cancelled = status.state is JobState.CANCELLED
        return (
            session_payload,
            no_update,
            events,
            _FORM_HIDDEN,
            _RUNTIME_VISIBLE,
            failed_view(status, cancelled=cancelled),
            _ACTIVITY_VISIBLE,
            _SUMMARY_HIDDEN,
            None,
            True,
            no_update,
            *untouched_errors,
            no_update,
        )


def _register_result_handoff_callback(app: dash.Dash) -> None:
    @app.callback(
        Output("q-location", "href"),
        Input(ResultIds.SESSION, "modified_timestamp"),
        State(ResultIds.SESSION, "data"),
        State(ElasticityIds.SESSION, "data"),
        State("q-location", "pathname"),
        prevent_initial_call=True,
    )
    def navigate_after_result_handoff(
        modified_timestamp: int | float | None,
        result_session: Mapping[str, Any] | None,
        workflow_session: Mapping[str, Any] | None,
        pathname: str | None,
    ) -> Any:
        del modified_timestamp
        if not _is_elasticity_result_handoff(
            result_session=result_session,
            workflow_session=workflow_session,
            pathname=pathname,
        ):
            return no_update
        return dash.get_relative_path("/results")


def _register_activity_callback(app: dash.Dash) -> None:
    @app.callback(
        Output(ElasticityIds.ACTIVITY_OUTPUT, "children"),
        Input(ElasticityIds.ACTIVITY_TABS, "value"),
        Input(ElasticityIds.EVENTS, "data"),
    )
    def render_activity(
        selected: str | None,
        events: Sequence[Mapping[str, Any]] | None,
    ) -> Any:
        return activity_view(events or (), selected or "all")


def _register_download_callbacks(
    app: dash.Dash,
    service: ElasticityWorkflowService,
) -> None:
    @app.callback(
        Output(ElasticityIds.DOWNLOAD_HDF5_PAYLOAD, "data"),
        Input(ElasticityIds.DOWNLOAD_HDF5, "n_clicks", allow_optional=True),
        State(ElasticityIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_hdf5(clicks: int | None, session: Mapping[str, Any] | None) -> Any:
        active = _active_from_session(clicks, session)
        if active is None:
            return no_update
        return dcc.send_file(
            service.results.path(active.reference),
            filename=active.reference.filename,
        )

    @app.callback(
        Output(ElasticityIds.DOWNLOAD_REPORT_PAYLOAD, "data"),
        Input(ElasticityIds.DOWNLOAD_REPORT, "n_clicks", allow_optional=True),
        State(ElasticityIds.SESSION, "data"),
        prevent_initial_call=True,
    )
    def download_report(clicks: int | None, session: Mapping[str, Any] | None) -> Any:
        active = _active_from_session(clicks, session)
        if active is None:
            return no_update
        stem = active.reference.filename.rsplit(".", 1)[0]
        return dcc.send_string(
            service.results.render_plain_report(active.reference),
            filename=f"{stem}-report.txt",
        )

    @app.callback(
        Output(ElasticityIds.DOWNLOAD_DIAGNOSTIC_PAYLOAD, "data"),
        Input(ElasticityIds.DOWNLOAD_DIAGNOSTIC, "n_clicks", allow_optional=True),
        State(ElasticityIds.SESSION, "data"),
        State(ElasticityIds.EVENTS, "data"),
        prevent_initial_call=True,
    )
    def download_diagnostic(
        clicks: int | None,
        session: Mapping[str, Any] | None,
        events: Sequence[Mapping[str, Any]] | None,
    ) -> Any:
        if not clicks:
            return no_update
        status = None if not session else session.get("status")
        status_mapping = status if isinstance(status, Mapping) else None
        return dcc.send_string(
            diagnostic_text(events or (), status_mapping),
            filename="elasticity-diagnostic.txt",
        )


def _active_from_session(
    clicks: int | None,
    session: Mapping[str, Any] | None,
) -> ActiveResultState | None:
    if not clicks or not session:
        return None
    value = session.get("active_result")
    if not isinstance(value, Mapping):
        return None
    return ActiveResultState.from_dict(dict(value))


def _component_default(field: Any) -> Any:
    if isinstance(field, MatrixField):
        return matrix_to_row_data(field)
    if isinstance(field, VectorField):
        return list(field.default or ())
    if isinstance(field, RangeTripletField):
        return list(field.default or ())
    if isinstance(field, TagsField):
        return [{"value": item} for item in (field.default or ())]
    if isinstance(field, BooleanField):
        return ["enabled"] if bool(field.default) else []
    if isinstance(field, ChoiceField) and field.kind in {
        FieldKind.MULTI_SELECT,
        FieldKind.CHECKLIST,
    }:
        return list(field.default or ())
    return field.default


def _field_class(field: Any, *, visible: bool) -> str:
    classes = ["q-field", f"q-field--{field.width}", f"q-field--{field.kind.value}"]
    if field.advanced:
        classes.append("q-field--advanced")
    if not visible:
        classes.append("is-hidden")
    return " ".join(classes)


def _orchestration_no_update(errors: Sequence[Any]) -> tuple[Any, ...]:
    return (
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        *errors,
        no_update,
    )


def _is_elasticity_result_handoff(
    *,
    result_session: Mapping[str, Any] | None,
    workflow_session: Mapping[str, Any] | None,
    pathname: str | None,
) -> bool:
    if dash.strip_relative_path(pathname) != "elasticity":
        return False
    if not isinstance(result_session, Mapping) or not isinstance(workflow_session, Mapping):
        return False
    workflow_result = workflow_session.get("active_result")
    return isinstance(workflow_result, Mapping) and dict(result_session) == dict(workflow_result)


__all__ = ["register_elasticity_callbacks"]
