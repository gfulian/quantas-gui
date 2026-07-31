"""Process-side Elasticity workflow using only ``quantas.api.elasticity``."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from quantas.api import elasticity, rendering

from quantas_gui.services.local_execution import WorkflowExecutionContext
from quantas_gui.workflows.elasticity.adapter import build_public_contracts
from quantas_gui.workflows.elasticity.request import ElasticityRequest


class _ElasticityObserver:
    """Translate Quantas events into bounded job events and global progress."""

    _PLANE_INDEX = {"xy": 0, "xz": 1, "yz": 2}

    def __init__(self, context: WorkflowExecutionContext, request: ElasticityRequest) -> None:
        self._context = context
        self._request = request

    def __call__(self, event: Any) -> None:
        self._context.checkpoint()
        level_value = getattr(getattr(event, "level", "info"), "value", None)
        level = str(level_value or getattr(event, "level", "info")).lower()
        message = str(getattr(event, "message", "Quantas event"))
        raw_progress = getattr(event, "progress", None)
        progress = self._global_progress(message, raw_progress)
        raw_data = getattr(event, "data", {})
        data = _lightweight_event_data(raw_data)
        self._context.emit(
            message[:1000],
            level=level,
            progress=progress,
            data=data,
        )

    def _global_progress(self, message: str, raw_progress: object) -> float | None:
        if not isinstance(raw_progress, (int, float)):
            return None
        value = min(1.0, max(0.0, float(raw_progress)))
        has_2d = self._request.calculate_2d
        has_3d = self._request.calculate_3d
        if message == "Three-dimensional elasticity sampling":
            start = 0.50 if has_2d else 0.10
            span = 0.45 if has_2d else 0.85
            return start + span * value
        plane = message.partition(":")[0].strip().lower()
        if plane in self._PLANE_INDEX:
            plane_progress = (self._PLANE_INDEX[plane] + value) / 3.0
            span = 0.40 if has_3d else 0.85
            return 0.10 + span * plane_progress
        return min(0.90, 0.10 + 0.80 * value)


def _lightweight_event_data(value: object) -> dict[str, object]:
    """Keep event metadata useful without persisting scientific arrays."""
    if not isinstance(value, Mapping):
        return {}
    data: dict[str, object] = {}
    for key in (
        "kind",
        "current",
        "total",
        "label",
        "plane",
        "property",
        "surface_count",
    ):
        item = value.get(key)
        if isinstance(item, (str, int, float, bool)) or item is None:
            data[key] = item

    kind = data.get("kind")
    result = value.get("result")
    if kind in {"input", "averages", "stability", "variations"} and result is not None:
        crystal_system = getattr(result, "crystal_system", None)
        if isinstance(crystal_system, str):
            data["crystal_system"] = crystal_system
    if kind == "stability" and result is not None:
        stability = getattr(result, "stability", None)
        is_stable = getattr(stability, "is_stable", None)
        if isinstance(is_stable, bool):
            data["is_stable"] = is_stable
    if kind == "rotation":
        rotation = value.get("rotation")
        rotation_kind = getattr(getattr(rotation, "kind", None), "value", None)
        if isinstance(rotation_kind, str):
            data["rotation_kind"] = rotation_kind
    return data


def run_elasticity_request(context: WorkflowExecutionContext) -> None:
    """Execute one persisted Elasticity request and write native HDF5 output."""
    with context.request_path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise ValueError("the persisted Elasticity request must be a mapping")
    request = ElasticityRequest.from_dict(value)
    context.emit("Building public Quantas Elasticity contracts", progress=0.05)
    input_data, options = build_public_contracts(
        request,
        workspace_path=context.workspace_path,
    )
    context.checkpoint()
    result = elasticity.run(
        input_data,
        options=options,
        observer=_ElasticityObserver(context, request),
    )
    context.checkpoint()
    payload = elasticity.get_result(result)
    context.emit(
        "Elasticity calculation completed",
        level="result",
        progress=0.95,
        data={
            "crystal_system": payload.crystal_system,
            "stable": None if payload.stability is None else payload.stability.is_stable,
            "warning_count": len(result.warnings),
        },
    )
    context.emit("Building deterministic report", progress=0.96)
    report_text = str(rendering.render_tables(elasticity.build_report(result)))
    context.emit("Writing native Quantas HDF5 result", progress=0.97)
    elasticity.write_result(result, context.output_path, report_text=report_text)
    context.checkpoint()


__all__ = ["run_elasticity_request"]
