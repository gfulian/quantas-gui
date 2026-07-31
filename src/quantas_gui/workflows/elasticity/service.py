"""Application service for Elasticity request persistence and result handoff."""

from __future__ import annotations

import json
import re
from base64 import b64decode
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import uuid4

import numpy as np

from quantas_gui.models import ActiveResultState
from quantas_gui.services.backends import (
    ExecutionBackend,
    JobEvent,
    JobHandle,
    JobState,
    JobStatus,
)
from quantas_gui.services.results import ResultExplorerService
from quantas_gui.services.workspaces import WorkspaceStore
from quantas_gui.workflows.elasticity.request import ElasticityRequest

_SAFE_DISPLAY = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True, slots=True)
class ImportedElasticityInput:
    """Small editable values extracted from one controlled source upload."""

    workspace_id: str
    source_filename: str
    jobname: str | None
    stiffness: tuple[tuple[float, ...], ...]


@dataclass(frozen=True, slots=True)
class ElasticityWorkflowService:
    """Coordinate controlled inputs, background execution, and Explorer handoff."""

    workspace_store: WorkspaceStore
    execution: ExecutionBackend
    results: ResultExplorerService
    max_upload_bytes: int = 256 * 1024 * 1024

    def create_workspace(self) -> str:
        """Create a workflow-owned workspace for an input or manual request."""
        return self.workspace_store.create_workspace()

    def store_input_bytes(
        self,
        *,
        workspace_id: str,
        filename: str,
        payload: bytes,
    ) -> str:
        """Store one Quantas text input atomically and return its safe basename."""
        safe_name = _input_filename(filename)
        destination = self.workspace_store.workspace_path(workspace_id) / "inputs" / safe_name
        with self.workspace_store.atomic_output(destination) as temporary:
            temporary.write_bytes(payload)
        return safe_name

    def import_upload(
        self,
        *,
        mode: Literal["quantas", "crystal", "vasp"],
        filename: str,
        contents: str,
        jobname: str = "Unknown",
        workspace_id: str | None = None,
    ) -> ImportedElasticityInput:
        """Parse a Quantas input or external output through the public API.

        The browser upload is decoded once, bounded, and written atomically below
        a controlled workflow workspace. External-code parsing deliberately uses
        ``quantas.api.elasticity.create_input`` rather than private readers.
        """
        if mode not in {"quantas", "crystal", "vasp"}:
            raise ValueError("choose Quantas input, CRYSTAL output, or VASP OUTCAR")
        payload = _decode_upload(contents)
        if len(payload) > self.max_upload_bytes:
            raise ValueError(
                f"the source file exceeds the {self.max_upload_bytes} byte upload limit"
            )
        owns_workspace = workspace_id is None
        resolved_workspace = workspace_id or self.create_workspace()
        try:
            safe_name = self.store_input_bytes(
                workspace_id=resolved_workspace,
                filename=filename,
                payload=payload,
            )
            source = self.workspace_store.workspace_path(resolved_workspace) / "inputs" / safe_name
            from quantas.api import elasticity

            if mode == "quantas":
                parsed = elasticity.read_input(source)
                imported_jobname: str | None = str(parsed.jobname)
            else:
                generated_name = _generated_input_filename(safe_name)
                generated = (
                    self.workspace_store.workspace_path(resolved_workspace)
                    / "inputs"
                    / generated_name
                )
                with self.workspace_store.atomic_output(generated) as temporary:
                    elasticity.create_input(
                        source,
                        temporary,
                        interface=mode,
                        jobname=jobname.strip() or "Unknown",
                    )
                parsed = elasticity.read_input(generated)
                imported_jobname = None
            if parsed.stiffness is None:
                raise ValueError("the imported source does not contain an elastic stiffness matrix")
            stiffness = np.asarray(parsed.stiffness, dtype=float)
            if stiffness.shape != (6, 6):
                raise ValueError("the imported stiffness matrix must have shape 6 × 6")
            matrix = tuple(tuple(float(value) for value in row) for row in stiffness.tolist())
            return ImportedElasticityInput(
                workspace_id=resolved_workspace,
                source_filename=safe_name,
                jobname=imported_jobname,
                stiffness=matrix,
            )
        except Exception:
            if owns_workspace:
                self.workspace_store.delete_workspace(resolved_workspace)
            raise

    def discard_workspace(self, workspace_id: str | None) -> None:
        """Delete an unused workflow workspace after reset or replacement."""
        if workspace_id:
            self.workspace_store.delete_workspace(workspace_id)

    def submit(
        self,
        request: ElasticityRequest,
        *,
        workspace_id: str | None = None,
    ) -> JobHandle:
        """Persist one request and immediately return its background-job handle."""
        owns_workspace = workspace_id is None
        resolved_workspace = workspace_id or self.workspace_store.create_workspace()
        request_path = (
            self.workspace_store.workspace_path(resolved_workspace)
            / "requests"
            / f"elasticity-{uuid4().hex}.json"
        )
        try:
            with self.workspace_store.atomic_output(request_path) as temporary:
                temporary.write_text(
                    json.dumps(request.as_dict(), ensure_ascii=False, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
            return self.execution.submit(
                module="elasticity",
                request_path=request_path,
                workspace_id=resolved_workspace,
            )
        except Exception:
            if owns_workspace:
                self.workspace_store.delete_workspace(resolved_workspace)
            raise

    def status(self, handle: JobHandle) -> JobStatus:
        """Return the latest persistent status."""
        return self.execution.status(handle)

    def events(
        self,
        handle: JobHandle,
        *,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> tuple[JobEvent, ...]:
        """Return ordered job events after a browser cursor."""
        return tuple(
            self.execution.events(
                handle,
                after_sequence=after_sequence,
                limit=limit,
            )
        )

    def cancel(self, handle: JobHandle) -> None:
        """Request cooperative cancellation."""
        self.execution.cancel(handle)

    def active_result(self, handle: JobHandle, *, jobname: str) -> ActiveResultState:
        """Register a successful native result and build the opaque Explorer handoff."""
        status = self.execution.status(handle)
        if status.state is not JobState.SUCCEEDED or status.result_id is None:
            raise RuntimeError("the Elasticity job has not produced a successful result")
        filename = f"{_result_stem(jobname)}_elasticity.hdf5"
        reference, overview = self.results.register_result(
            workspace_id=handle.workspace_id,
            result_id=status.result_id,
            filename=filename,
            disposable_workspace=False,
        )
        return ActiveResultState(reference=reference, summary=overview.summary)


def _input_filename(value: str) -> str:
    candidate = Path(value.replace("\\", "/")).name.strip()
    candidate = _SAFE_DISPLAY.sub("-", candidate).strip("-._")
    if not candidate:
        raise ValueError("input filename has no safe characters")
    return candidate[:240]


def _result_stem(jobname: str) -> str:
    candidate = _SAFE_DISPLAY.sub("-", jobname.strip()).strip("-._")
    return (candidate or "elasticity")[:120]


def _decode_upload(contents: str) -> bytes:
    if not isinstance(contents, str) or "," not in contents:
        raise ValueError("the browser upload payload is malformed")
    header, encoded = contents.split(",", 1)
    if ";base64" not in header.lower():
        raise ValueError("the browser upload payload is not base64 encoded")
    try:
        return b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("the browser upload payload could not be decoded") from exc


def _generated_input_filename(source_filename: str) -> str:
    stem = Path(source_filename).stem or "elasticity"
    safe_stem = _SAFE_DISPLAY.sub("-", stem).strip("-._") or "elasticity"
    return f"{safe_stem[:180]}-quantas.dat"


__all__ = ["ElasticityWorkflowService", "ImportedElasticityInput"]
