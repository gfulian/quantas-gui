"""Safe lightweight serialization helpers for GUI inspection views."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


_MAX_INLINE_SEQUENCE = 24
_MAX_DEPTH = 5


def to_json_value(value: Any, *, depth: int = 0) -> Any:
    """Return a bounded JSON-compatible view without expanding large arrays.

    Parameters
    ----------
    value
        Arbitrary value restored from a public Quantas result contract.
    depth
        Current recursion depth used internally.

    Returns
    -------
    object
        JSON-compatible scalar, mapping, sequence, or structural summary.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return to_json_value(value.value, depth=depth + 1)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)

    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    if shape is not None and dtype is not None:
        return {
            "type": type(value).__name__,
            "shape": [int(item) for item in tuple(shape)],
            "dtype": str(dtype),
        }

    if depth >= _MAX_DEPTH:
        return {"type": type(value).__name__, "summary": "maximum inspection depth reached"}

    if isinstance(value, Mapping):
        return {
            str(key): to_json_value(item, depth=depth + 1)
            for key, item in value.items()
        }

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) <= _MAX_INLINE_SEQUENCE:
            return [to_json_value(item, depth=depth + 1) for item in value]
        return {
            "type": type(value).__name__,
            "length": len(value),
            "preview": [
                to_json_value(item, depth=depth + 1)
                for item in value[: min(5, len(value))]
            ],
        }

    if is_dataclass(value):
        return {
            field.name: to_json_value(getattr(value, field.name), depth=depth + 1)
            for field in fields(value)
        }

    if hasattr(value, "as_dict") and callable(value.as_dict):
        try:
            return to_json_value(value.as_dict(), depth=depth + 1)
        except Exception:
            pass

    return {"type": type(value).__name__}


def inventory_item(key: str, value: Any) -> dict[str, Any]:
    """Return a structural inventory record for one result payload value."""
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    summary: str | None = None

    if shape is None and isinstance(value, Mapping):
        summary = f"{len(value)} entries"
    elif shape is None and isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        summary = f"{len(value)} items"
    elif shape is None and is_dataclass(value):
        summary = f"{len(fields(value))} fields"
    elif value is None or isinstance(value, (str, int, float, bool)):
        summary = str(value)

    return {
        "key": str(key),
        "value_type": type(value).__name__,
        "shape": None if shape is None else tuple(int(item) for item in tuple(shape)),
        "dtype": None if dtype is None else str(dtype),
        "summary": summary,
    }
