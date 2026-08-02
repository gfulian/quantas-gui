"""Serializable server-side request contract for the SEISMIC workflow."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, cast

from quantas_gui.workflows.common import RotationRequest

HemisphereRequest = Literal["upper", "lower", "full"]
SamplingLevelRequest = Literal["phase", "group", "enhancement"]

_SUPPORTED_HEMISPHERES = frozenset({"upper", "lower", "full"})
_SUPPORTED_LEVELS = frozenset({"phase", "group", "enhancement"})


@dataclass(frozen=True, slots=True)
class SeismicRequest:
    """Complete server-side request for one public Quantas SEISMIC run.

    Manual requests provide both ``stiffness`` and ``density``. File-backed
    requests provide only ``input_filename``. Filenames are controlled
    basenames below the workflow workspace, never arbitrary server paths.
    """

    jobname: str
    stiffness: tuple[tuple[float, ...], ...] | None = None
    density: float | None = None
    input_filename: str | None = None
    source_filename: str | None = None
    ntheta: int = 91
    nphi: int = 181
    hemisphere: HemisphereRequest = "upper"
    level: SamplingLevelRequest = "enhancement"
    batch_size: int = 512
    track_polarization_axes: bool = True
    eigenvalue_rtol: float = 1.0e-10
    eigenvalue_atol: float = 1.0e-12
    degeneracy_rtol: float = 1.0e-8
    degeneracy_atol: float = 1.0e-10
    pseudoinverse_rcond: float = 1.0e-10
    caustic_rtol: float = 1.0e-10
    caustic_atol: float = 1.0e-12
    rotation: RotationRequest | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        jobname = self.jobname.strip()
        if not jobname:
            raise ValueError("jobname must not be empty")
        object.__setattr__(self, "jobname", jobname)

        manual = self.stiffness is not None or self.density is not None
        file_backed = self.input_filename is not None
        if manual == file_backed:
            raise ValueError("provide exactly one manual medium or input file")
        if manual:
            if self.stiffness is None or self.density is None:
                raise ValueError("manual SEISMIC input requires stiffness and density")
            object.__setattr__(self, "stiffness", _matrix6(self.stiffness))
            density = float(self.density)
            if not math.isfinite(density) or density <= 0.0:
                raise ValueError("density must be finite and positive")
            object.__setattr__(self, "density", density)
        else:
            assert self.input_filename is not None
            object.__setattr__(self, "input_filename", _safe_input_filename(self.input_filename))

        if self.source_filename is not None:
            object.__setattr__(
                self,
                "source_filename",
                _safe_input_filename(self.source_filename),
            )
        if self.ntheta < 2:
            raise ValueError("ntheta must be at least 2")
        if self.nphi < 3:
            raise ValueError("nphi must be at least 3")
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")
        if self.hemisphere not in _SUPPORTED_HEMISPHERES:
            raise ValueError("hemisphere must be upper, lower, or full")
        if self.level not in _SUPPORTED_LEVELS:
            raise ValueError("level must be phase, group, or enhancement")
        if not isinstance(self.track_polarization_axes, bool):
            raise ValueError("track_polarization_axes must be a boolean")

        for name in (
            "eigenvalue_rtol",
            "eigenvalue_atol",
            "degeneracy_rtol",
            "degeneracy_atol",
            "caustic_rtol",
            "caustic_atol",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
            object.__setattr__(self, name, value)
        pseudoinverse_rcond = float(self.pseudoinverse_rcond)
        if not math.isfinite(pseudoinverse_rcond) or not 0.0 <= pseudoinverse_rcond < 1.0:
            raise ValueError("pseudoinverse_rcond must be in the interval [0, 1)")
        object.__setattr__(self, "pseudoinverse_rcond", pseudoinverse_rcond)
        if self.schema_version != 1:
            raise ValueError("unsupported SEISMIC request schema")

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible request without filesystem paths."""
        value = asdict(self)
        value["stiffness"] = (
            None if self.stiffness is None else [list(row) for row in self.stiffness]
        )
        value["rotation"] = None if self.rotation is None else self.rotation.as_dict()
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> SeismicRequest:
        """Restore and validate a persisted request mapping."""
        stiffness = value.get("stiffness")
        normalized_stiffness: tuple[tuple[float, ...], ...] | None = None
        if stiffness is not None:
            if not isinstance(stiffness, Sequence) or isinstance(stiffness, (str, bytes)):
                raise ValueError("stiffness must be a matrix")
            rows: list[tuple[float, ...]] = []
            for row in stiffness:
                if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
                    raise ValueError("stiffness rows must be sequences")
                rows.append(tuple(float(item) for item in row))
            normalized_stiffness = tuple(rows)

        rotation_value = value.get("rotation")
        rotation = None
        if rotation_value is not None:
            if not isinstance(rotation_value, Mapping):
                raise ValueError("rotation must be a mapping")
            rotation = RotationRequest.from_dict(rotation_value)

        raw_hemisphere = str(value.get("hemisphere", "upper"))
        if raw_hemisphere not in _SUPPORTED_HEMISPHERES:
            raise ValueError("hemisphere must be upper, lower, or full")
        hemisphere = cast(HemisphereRequest, raw_hemisphere)
        raw_level = str(value.get("level", "enhancement"))
        if raw_level not in _SUPPORTED_LEVELS:
            raise ValueError("level must be phase, group, or enhancement")
        level = cast(SamplingLevelRequest, raw_level)

        density_value = value.get("density")
        return cls(
            jobname=str(value.get("jobname", "")),
            stiffness=normalized_stiffness,
            density=None if density_value is None else float(density_value),
            input_filename=(
                None if value.get("input_filename") is None else str(value["input_filename"])
            ),
            source_filename=(
                None if value.get("source_filename") is None else str(value["source_filename"])
            ),
            ntheta=int(value.get("ntheta", 91)),
            nphi=int(value.get("nphi", 181)),
            hemisphere=hemisphere,
            level=level,
            batch_size=int(value.get("batch_size", 512)),
            track_polarization_axes=_boolean(
                value.get("track_polarization_axes"),
                default=True,
            ),
            eigenvalue_rtol=float(value.get("eigenvalue_rtol", 1.0e-10)),
            eigenvalue_atol=float(value.get("eigenvalue_atol", 1.0e-12)),
            degeneracy_rtol=float(value.get("degeneracy_rtol", 1.0e-8)),
            degeneracy_atol=float(value.get("degeneracy_atol", 1.0e-10)),
            pseudoinverse_rcond=float(value.get("pseudoinverse_rcond", 1.0e-10)),
            caustic_rtol=float(value.get("caustic_rtol", 1.0e-10)),
            caustic_atol=float(value.get("caustic_atol", 1.0e-12)),
            rotation=rotation,
            schema_version=int(value.get("schema_version", 1)),
        )


def _boolean(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError("expected a boolean")
    return value


def _matrix6(value: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    rows = tuple(tuple(float(item) for item in row) for row in value)
    if len(rows) != 6 or any(len(row) != 6 for row in rows):
        raise ValueError("stiffness must have shape (6, 6)")
    if not all(math.isfinite(item) for row in rows for item in row):
        raise ValueError("stiffness values must be finite")
    return rows


def _safe_input_filename(value: str) -> str:
    filename = value.strip()
    if not filename or filename in {".", ".."}:
        raise ValueError("input filename must not be empty")
    if Path(filename).name != filename or any(separator in filename for separator in ("/", "\\")):
        raise ValueError("input filename must be a basename")
    if len(filename) > 240:
        raise ValueError("input filename is too long")
    return filename


__all__ = [
    "HemisphereRequest",
    "SamplingLevelRequest",
    "SeismicRequest",
]
