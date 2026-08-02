"""Serializable physical tensor-rotation request shared by workflows."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class RotationRequest:
    """Describe one physical source-to-analysis tensor transformation."""

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


__all__ = ["RotationRequest"]
