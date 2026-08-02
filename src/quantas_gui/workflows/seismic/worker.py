"""Process-side SEISMIC workflow using only ``quantas.api.seismic``."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from quantas.api import rendering, seismic

from quantas_gui.services.local_execution import WorkflowExecutionContext
from quantas_gui.workflows.seismic.adapter import build_public_contracts
from quantas_gui.workflows.seismic.request import SeismicRequest


class _SeismicObserver:
    """Translate Quantas events into bounded job events and global progress."""

    def __init__(self, context: WorkflowExecutionContext) -> None:
        self._context = context

    def __call__(self, event: Any) -> None:
        self._context.checkpoint()
        level_value = getattr(getattr(event, "level", "info"), "value", None)
        level = str(level_value or getattr(event, "level", "info")).lower()
        message = str(getattr(event, "message", "Quantas event"))
        raw_progress = getattr(event, "progress", None)
        progress = _global_progress(raw_progress)
        data = _lightweight_event_data(getattr(event, "data", {}))
        self._context.emit(
            message[:1000],
            level=level,
            progress=progress,
            data=data,
        )


def _global_progress(raw_progress: object) -> float | None:
    if not isinstance(raw_progress, (int, float)) or isinstance(raw_progress, bool):
        return None
    value = min(1.0, max(0.0, float(raw_progress)))
    return 0.10 + 0.84 * value


def _lightweight_event_data(value: object) -> dict[str, object]:
    """Keep useful scalar metadata without persisting scientific arrays."""
    if not isinstance(value, Mapping):
        return {}
    data: dict[str, object] = {}
    for key in (
        "kind",
        "current",
        "total",
        "level",
        "n_points",
        "invalid_phase_points",
        "degenerate_mode_points",
        "shear_acoustic_axis_candidates",
        "caustic_candidates",
        "non_finite_enhancement_points",
    ):
        item = value.get(key)
        if isinstance(item, (str, int, float, bool)) or item is None:
            data[key] = item

    if data.get("kind") == "isotropic_reference":
        velocities = value.get("velocities")
        shear = getattr(velocities, "shear", None)
        compressional = getattr(velocities, "compressional", None)
        if isinstance(shear, (int, float)):
            data["isotropic_shear_km_s"] = float(shear)
        if isinstance(compressional, (int, float)):
            data["isotropic_compressional_km_s"] = float(compressional)
    if data.get("kind") == "seismic_field":
        diagnostics = value.get("diagnostics")
        if isinstance(diagnostics, Mapping):
            for key in (
                "n_points",
                "invalid_phase_points",
                "degenerate_mode_points",
                "shear_acoustic_axis_candidates",
                "caustic_candidates",
                "non_finite_enhancement_points",
            ):
                item = diagnostics.get(key)
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    data[key] = item
    return data


def run_seismic_request(context: WorkflowExecutionContext) -> None:
    """Execute one persisted SEISMIC request and write native HDF5 output."""
    with context.request_path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise ValueError("the persisted SEISMIC request must be a mapping")
    request = SeismicRequest.from_dict(value)
    context.emit("Building public Quantas SEISMIC contracts", progress=0.05)
    input_data, options = build_public_contracts(
        request,
        workspace_path=context.workspace_path,
    )
    context.checkpoint()
    result = seismic.run(
        input_data,
        options=options,
        observer=_SeismicObserver(context),
    )
    context.checkpoint()
    payload = seismic.get_result(result)
    metadata = payload.metadata
    context.emit(
        "SEISMIC calculation completed",
        level="result",
        progress=0.95,
        data={
            "density_kg_m3": payload.density,
            "level": payload.field.level.value,
            "n_points": payload.field.n_points,
            "warning_count": len(result.warnings),
            "invalid_phase_points": int(metadata.get("invalid_phase_points", 0)),
            "degenerate_mode_points": int(metadata.get("degenerate_mode_points", 0)),
            "shear_acoustic_axis_candidates": int(
                metadata.get("shear_acoustic_axis_candidates", 0)
            ),
            "caustic_candidates": int(metadata.get("caustic_candidates", 0)),
            "non_finite_enhancement_points": int(metadata.get("non_finite_enhancement_points", 0)),
        },
    )
    context.emit("Building deterministic report", progress=0.96)
    report_text = str(rendering.render_tables(seismic.build_report(result)))
    context.emit("Writing native Quantas HDF5 result", progress=0.97)
    seismic.write_result(result, context.output_path, report_text=report_text)
    context.checkpoint()


__all__ = ["run_seismic_request"]
