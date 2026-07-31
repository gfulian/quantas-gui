"""Serializable server-side request contract for the Elasticity workflow."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

_SUPPORTED_PROPERTIES = frozenset({"young", "compressibility", "shear", "poisson"})


@dataclass(frozen=True, slots=True)
class RotationRequest:
    """Serializable physical tensor rotation requested by the user."""

    kind: Literal["xyz", "matrix"]
    values: tuple[float, ...]
    description: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"xyz", "matrix"}:
            raise ValueError("rotation kind must be 'xyz' or 'matrix'")
        values = tuple(float(value) for value in self.values)
        expected = 3 if self.kind == "xyz" else 9
        if len(values) != expected:
            raise ValueError(f"{self.kind} rotation requires {expected} values")
        if not all(math.isfinite(value) for value in values):
            raise ValueError("rotation values must be finite")
        object.__setattr__(self, "values", values)
        if self.description is not None and not self.description.strip():
            object.__setattr__(self, "description", None)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return {
            "kind": self.kind,
            "values": list(self.values),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> RotationRequest:
        """Restore a rotation request from persisted JSON."""
        raw_values = value.get("values", ())
        if not isinstance(raw_values, Sequence) or isinstance(raw_values, (str, bytes)):
            raise ValueError("rotation values must be a sequence")
        raw_kind = str(value.get("kind", ""))
        if raw_kind == "xyz":
            kind: Literal["xyz", "matrix"] = "xyz"
        elif raw_kind == "matrix":
            kind = "matrix"
        else:
            raise ValueError("rotation kind must be 'xyz' or 'matrix'")
        description = value.get("description")
        return cls(
            kind=kind,
            values=tuple(float(item) for item in raw_values),
            description=None if description is None else str(description),
        )


@dataclass(frozen=True, slots=True)
class ElasticityRequest:
    """Complete server-side request for one public Quantas Elasticity run.

    Exactly one of ``stiffness`` and ``input_filename`` is required. The
    filename is a basename inside the controlled ``inputs`` directory, never an
    arbitrary server path.
    """

    jobname: str
    stiffness: tuple[tuple[float, ...], ...] | None = None
    input_filename: str | None = None
    source_filename: str | None = None
    calculate_2d: bool = False
    ntheta_2d: int = 361
    calculate_3d: bool = False
    ntheta_3d: int = 61
    nphi_3d: int = 121
    properties_3d: tuple[str, ...] = ("young", "compressibility", "shear", "poisson")
    batch_size: int = 65536
    rotation: RotationRequest | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        jobname = self.jobname.strip()
        if not jobname:
            raise ValueError("jobname must not be empty")
        object.__setattr__(self, "jobname", jobname)
        if (self.stiffness is None) == (self.input_filename is None):
            raise ValueError("provide exactly one stiffness matrix or input file")
        if self.stiffness is not None:
            matrix = _matrix6(self.stiffness)
            object.__setattr__(self, "stiffness", matrix)
        if self.input_filename is not None:
            filename = _safe_input_filename(self.input_filename)
            object.__setattr__(self, "input_filename", filename)
        if self.source_filename is not None:
            source_filename = _safe_input_filename(self.source_filename)
            object.__setattr__(self, "source_filename", source_filename)
        if self.ntheta_2d < 2:
            raise ValueError("ntheta_2d must be at least 2")
        if self.ntheta_3d < 2:
            raise ValueError("ntheta_3d must be at least 2")
        if self.nphi_3d < 3:
            raise ValueError("nphi_3d must be at least 3")
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")
        selected: list[str] = []
        for property_name in self.properties_3d:
            if property_name not in _SUPPORTED_PROPERTIES:
                raise ValueError(f"unsupported 3D elasticity property: {property_name}")
            if property_name not in selected:
                selected.append(property_name)
        if self.calculate_3d and not selected:
            raise ValueError("select at least one 3D elasticity property")
        object.__setattr__(self, "properties_3d", tuple(selected))
        if self.schema_version != 1:
            raise ValueError("unsupported elasticity request schema")

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible request without filesystem paths."""
        value = asdict(self)
        value["stiffness"] = (
            None if self.stiffness is None else [list(row) for row in self.stiffness]
        )
        value["properties_3d"] = list(self.properties_3d)
        value["rotation"] = None if self.rotation is None else self.rotation.as_dict()
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ElasticityRequest:
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
        raw_properties = value.get(
            "properties_3d", ("young", "compressibility", "shear", "poisson")
        )
        if not isinstance(raw_properties, Sequence) or isinstance(raw_properties, (str, bytes)):
            raise ValueError("properties_3d must be a sequence")
        return cls(
            jobname=str(value.get("jobname", "")),
            stiffness=normalized_stiffness,
            input_filename=(
                None if value.get("input_filename") is None else str(value["input_filename"])
            ),
            source_filename=(
                None if value.get("source_filename") is None else str(value["source_filename"])
            ),
            calculate_2d=_boolean(value.get("calculate_2d"), default=False),
            ntheta_2d=int(value.get("ntheta_2d", 361)),
            calculate_3d=_boolean(value.get("calculate_3d"), default=False),
            ntheta_3d=int(value.get("ntheta_3d", 61)),
            nphi_3d=int(value.get("nphi_3d", 121)),
            properties_3d=tuple(str(item) for item in raw_properties),
            batch_size=int(value.get("batch_size", 65536)),
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
    # Symmetry tolerance is scientific validation owned by Quantas. The GUI
    # request layer checks only shape and finite numerical values.
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


__all__ = ["ElasticityRequest", "RotationRequest"]
