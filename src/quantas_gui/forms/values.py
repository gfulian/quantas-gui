"""Value-property bindings and data adapters for declarative forms."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .ids import FormIds
from .schema import (
    FieldKind,
    FieldSpec,
    FileUploadField,
    KeyValueField,
    MatrixField,
    RangeTripletField,
    TagsField,
    VectorField,
)


def value_property(field: FieldSpec) -> str:
    """Return the Dash property carrying the raw value of one field."""
    if isinstance(field, (MatrixField, KeyValueField, TagsField)):
        return "rowData"
    if isinstance(field, (RangeTripletField, VectorField)):
        return "data"
    if isinstance(field, FileUploadField):
        return "contents"
    return "value"


def value_component_id(form: str, field: FieldSpec) -> dict[str, Any]:
    """Return the component identifier that carries one field's value."""
    if isinstance(field, RangeTripletField):
        return FormIds.control(form, field.key, "triplet-store")
    if isinstance(field, VectorField):
        return FormIds.control(form, field.key, "vector-store")
    if isinstance(field, FileUploadField):
        return {"type": "q-form-upload", "form": form, "field": field.key}
    return FormIds.control(form, field.key)


def matrix_to_row_data(
    field: MatrixField,
    value: Sequence[Sequence[float]] | None = None,
) -> list[dict[str, Any]]:
    """Convert a matrix into Dash AG Grid row records."""
    matrix = value if value is not None else field.default
    if matrix is None:
        matrix = tuple(tuple(0.0 for _ in range(field.columns)) for _ in range(field.rows))
    records: list[dict[str, Any]] = []
    for row_index in range(field.rows):
        label = field.row_labels[row_index] if field.row_labels else str(row_index + 1)
        record: dict[str, Any] = {"__row__": label}
        for column_index in range(field.columns):
            record[f"c{column_index}"] = float(matrix[row_index][column_index])
        records.append(record)
    return records


def row_data_to_matrix(
    field: MatrixField,
    rows: Sequence[Mapping[str, Any]] | None,
) -> tuple[tuple[float, ...], ...] | None:
    """Convert Dash AG Grid row records back to a numeric matrix."""
    if rows is None:
        return None
    return tuple(
        tuple(float(row.get(f"c{column_index}")) for column_index in range(field.columns))
        for row in rows
    )


def key_value_to_row_data(field: KeyValueField) -> list[dict[str, Any]]:
    """Convert a key/value default into editable grid rows."""
    if field.default is None:
        return []
    if isinstance(field.default, Mapping):
        return [{"key": str(key), "value": value} for key, value in field.default.items()]
    return [dict(item) for item in field.default]


def normalize_component_value(field: FieldSpec, raw: Any) -> Any:
    """Normalize widget-specific data into the value expected by validation."""
    if isinstance(field, MatrixField):
        return row_data_to_matrix(field, raw)
    if isinstance(field, KeyValueField):
        return tuple(dict(item) for item in (raw or ()))
    if isinstance(field, TagsField):
        return tuple(
            item.get("value")
            for item in (raw or ())
            if item.get("value") not in (None, "")
        )
    if field.kind is FieldKind.BOOLEAN:
        # A one-option checklist represents false as [] and true as ["enabled"].
        if isinstance(raw, list):
            return bool(raw)
    return raw


__all__ = [
    "key_value_to_row_data",
    "matrix_to_row_data",
    "normalize_component_value",
    "row_data_to_matrix",
    "value_component_id",
    "value_property",
]
