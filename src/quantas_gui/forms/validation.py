"""Pure validation for declarative Quantas GUI forms."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any

from .schema import (
    BooleanField,
    ChoiceField,
    Condition,
    ConditionOperator,
    FieldKind,
    FieldSpec,
    FileUploadField,
    FormRuleKind,
    FormSchema,
    KeyValueField,
    MatrixField,
    NumericField,
    RangeTripletField,
    SliderField,
    TagsField,
    TextField,
    VectorField,
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One actionable form-validation issue."""

    field: str | None
    message: str
    code: str
    severity: str = "error"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Collection of normalized values and validation issues."""

    values: Mapping[str, Any]
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        """Return whether no error-level issue is present."""
        return not any(issue.severity == "error" for issue in self.issues)

    def for_field(self, field: str) -> tuple[ValidationIssue, ...]:
        """Return issues associated with one field key."""
        return tuple(issue for issue in self.issues if issue.field == field)


def evaluate_condition(condition: Condition, values: Mapping[str, Any]) -> bool:
    """Evaluate one declarative condition against current values."""
    current = values.get(condition.field)
    operator = condition.operator
    if operator is ConditionOperator.EQUALS:
        return current == condition.value
    if operator is ConditionOperator.NOT_EQUALS:
        return current != condition.value
    if operator is ConditionOperator.IN:
        return current in _as_collection(condition.value)
    if operator is ConditionOperator.NOT_IN:
        return current not in _as_collection(condition.value)
    if operator is ConditionOperator.TRUTHY:
        return bool(current)
    if operator is ConditionOperator.FALSY:
        return not bool(current)
    if operator is ConditionOperator.IS_NONE:
        return current is None
    if operator is ConditionOperator.IS_NOT_NONE:
        return current is not None
    raise ValueError(f"unsupported condition operator: {operator}")


def conditions_match(
    conditions: Sequence[Condition],
    values: Mapping[str, Any],
) -> bool:
    """Return whether all conditions match current values."""
    return all(evaluate_condition(condition, values) for condition in conditions)


def field_is_visible(field: FieldSpec, values: Mapping[str, Any]) -> bool:
    """Return the current visibility of one field."""
    return conditions_match(field.visible_when, values)


def field_is_enabled(field: FieldSpec, values: Mapping[str, Any]) -> bool:
    """Return the current enablement of one field."""
    return not field.disabled and conditions_match(field.enabled_when, values)


def validate_form(schema: FormSchema, values: Mapping[str, Any]) -> ValidationResult:
    """Validate and normalize a raw form-value mapping.

    This validation provides immediate frontend feedback. Constructing the
    corresponding Quantas API dataclass remains the final scientific and
    numerical validation boundary.
    """
    normalized: dict[str, Any] = {}
    issues: list[ValidationIssue] = []

    current = {field.key: values.get(field.key, field.default) for field in schema.fields}
    for field in schema.fields:
        if not field_is_visible(field, current):
            normalized[field.key] = None
            continue
        value, field_issues = validate_field(field, current.get(field.key))
        normalized[field.key] = value
        issues.extend(field_issues)

    for rule in schema.rules:
        if rule.when and not conditions_match(rule.when, normalized):
            continue
        populated = [key for key in rule.fields if not _is_empty(normalized.get(key))]
        if rule.kind is FormRuleKind.EXACTLY_ONE and len(populated) != 1:
            issues.append(ValidationIssue(None, rule.message, "exactly-one"))
        elif rule.kind is FormRuleKind.AT_LEAST_ONE and not populated:
            issues.append(ValidationIssue(None, rule.message, "at-least-one"))
        elif rule.kind is FormRuleKind.MUTUALLY_EXCLUSIVE and len(populated) > 1:
            issues.append(ValidationIssue(None, rule.message, "mutually-exclusive"))
        elif rule.kind is FormRuleKind.REQUIRES:
            head, *required = rule.fields
            if not _is_empty(normalized.get(head)) and any(
                _is_empty(normalized.get(item)) for item in required
            ):
                issues.append(ValidationIssue(None, rule.message, "requires"))

    return ValidationResult(values=normalized, issues=tuple(issues))


def validate_field(
    field: FieldSpec,
    value: Any,
) -> tuple[Any, tuple[ValidationIssue, ...]]:
    """Validate and normalize one field value."""
    if _is_empty(value):
        if field.required:
            return value, (ValidationIssue(field.key, "This field is required.", "required"),)
        return None, ()

    try:
        if isinstance(field, TextField):
            text_value = str(value)
            if field.max_length is not None and len(text_value) > field.max_length:
                return text_value, (
                    ValidationIssue(
                        field.key,
                        f"Use at most {field.max_length} characters.",
                        "max-length",
                    ),
                )
            return text_value, ()
        if isinstance(field, NumericField):
            numeric_value = _number(value, integer=field.kind is FieldKind.INTEGER)
            return numeric_value, _numeric_issues(field.key, numeric_value, field.bounds)
        if isinstance(field, BooleanField):
            return bool(value), ()
        if isinstance(field, ChoiceField):
            allowed = {item.value for item in field.choices if not item.disabled}
            if field.kind in {FieldKind.MULTI_SELECT, FieldKind.CHECKLIST}:
                selected = tuple(value or ())
                unknown = [item for item in selected if item not in allowed]
                if unknown:
                    return selected, (
                        ValidationIssue(
                            field.key,
                            f"Unsupported selections: {unknown!r}.",
                            "choice",
                        ),
                    )
                return selected, ()
            if value not in allowed:
                return value, (
                    ValidationIssue(field.key, "Choose one supported option.", "choice"),
                )
            return value, ()
        if isinstance(field, SliderField):
            if field.kind is FieldKind.RANGE_SLIDER:
                selected = tuple(_number(item) for item in value)
                if len(selected) != 2:
                    raise ValueError("range slider requires two values")
                issues = tuple(
                    issue
                    for item in selected
                    for issue in _numeric_issues(field.key, item, field.bounds)
                )
                if selected[0] > selected[1]:
                    issues += (
                        ValidationIssue(
                            field.key,
                            "The lower slider value cannot exceed the upper value.",
                            "range-order",
                        ),
                    )
                return selected, issues
            scalar = _number(value)
            return scalar, _numeric_issues(field.key, scalar, field.bounds)
        if isinstance(field, RangeTripletField):
            selected = tuple(_number(item) for item in value)
            if len(selected) != 3:
                raise ValueError("range triplet requires start, stop, and step")
            start, stop, step = selected
            flat = tuple(
                issue
                for item in selected
                for issue in _numeric_issues(field.key, item, field.bounds)
            )
            if step == 0:
                flat += (ValidationIssue(field.key, "Step cannot be zero.", "zero-step"),)
            elif start < stop and step < 0:
                flat += (
                    ValidationIssue(
                        field.key,
                        "Step must be positive for an increasing range.",
                        "step-direction",
                    ),
                )
            elif start > stop and step > 0:
                flat += (
                    ValidationIssue(
                        field.key,
                        "Step must be negative for a decreasing range.",
                        "step-direction",
                    ),
                )
            return selected, flat
        if isinstance(field, VectorField):
            selected = tuple(_number(item) for item in value)
            if len(selected) != field.length:
                return selected, (
                    ValidationIssue(
                        field.key,
                        f"Expected {field.length} values.",
                        "vector-length",
                    ),
                )
            issues = tuple(
                issue
                for item in selected
                for issue in _numeric_issues(field.key, item, field.bounds)
            )
            return selected, issues
        if isinstance(field, MatrixField):
            matrix = _matrix(value, field.rows, field.columns)
            issues = tuple(
                issue
                for row in matrix
                for item in row
                for issue in _numeric_issues(field.key, item, field.bounds)
            )
            if field.symmetric and not _is_symmetric(matrix, field.symmetry_tolerance):
                issues += (
                    ValidationIssue(
                        field.key,
                        f"Matrix must be symmetric within {field.symmetry_tolerance:g}.",
                        "matrix-symmetry",
                    ),
                )
            return matrix, issues
        if isinstance(field, FileUploadField):
            return value, ()
        if isinstance(field, TagsField):
            return tuple(_typed(item, field.value_type) for item in value), ()
        if isinstance(field, KeyValueField):
            rows = tuple(dict(item) for item in value)
            issues = _validate_key_value(field, rows)
            return rows, issues
    except (TypeError, ValueError, OverflowError) as exc:
        return value, (ValidationIssue(field.key, str(exc), "invalid-value"),)

    raise TypeError(f"unsupported field specification: {type(field).__name__}")


def _numeric_issues(key: str, value: float | int, bounds: Any) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    if not isfinite(float(value)):
        issues.append(ValidationIssue(key, "Value must be finite.", "finite"))
        return tuple(issues)
    if bounds.minimum is not None:
        too_low = value <= bounds.minimum if bounds.minimum_open else value < bounds.minimum
        if too_low:
            relation = "greater than" if bounds.minimum_open else "at least"
            issues.append(
                ValidationIssue(key, f"Value must be {relation} {bounds.minimum:g}.", "minimum")
            )
    if bounds.maximum is not None:
        too_high = value >= bounds.maximum if bounds.maximum_open else value > bounds.maximum
        if too_high:
            relation = "less than" if bounds.maximum_open else "at most"
            issues.append(
                ValidationIssue(key, f"Value must be {relation} {bounds.maximum:g}.", "maximum")
            )
    return tuple(issues)


def _validate_key_value(
    field: KeyValueField,
    rows: Sequence[Mapping[str, Any]],
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    keys: list[str] = []
    for index, row in enumerate(rows, start=1):
        key = str(row.get("key", "")).strip()
        if not key:
            issues.append(ValidationIssue(field.key, f"Row {index} has no key.", "missing-key"))
            continue
        keys.append(key)
        try:
            _typed(row.get("value"), field.value_type)
        except (TypeError, ValueError) as exc:
            issues.append(ValidationIssue(field.key, f"Row {index}: {exc}", "invalid-value"))
    if not field.allow_duplicate_keys and len(keys) != len(set(keys)):
        issues.append(ValidationIssue(field.key, "Keys must be unique.", "duplicate-key"))
    return tuple(issues)


def _matrix(value: Any, rows: int, columns: int) -> tuple[tuple[float, ...], ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        matrix = tuple(tuple(_number(item) for item in row) for row in value)
    else:
        raise ValueError("matrix value must be a sequence of rows")
    if len(matrix) != rows or any(len(row) != columns for row in matrix):
        raise ValueError(f"matrix must have shape ({rows}, {columns})")
    return matrix


def _is_symmetric(matrix: Sequence[Sequence[float]], tolerance: float) -> bool:
    return all(
        abs(matrix[i][j] - matrix[j][i]) <= tolerance
        for i in range(len(matrix))
        for j in range(i + 1, len(matrix))
    )


def _typed(value: Any, value_type: str) -> str | int | float:
    if value_type == "text":
        return str(value)
    if value_type == "integer":
        return int(value)
    if value_type == "float":
        return float(value)
    raise ValueError(f"unsupported value type: {value_type}")


def _number(value: Any, *, integer: bool = False) -> int | float:
    if isinstance(value, bool):
        raise ValueError("boolean values are not valid numbers")
    numeric = float(value)
    if integer:
        if not numeric.is_integer():
            raise ValueError("value must be an integer")
        return int(numeric)
    return numeric


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == () or value == [] or value == {}


def _as_collection(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return (value,)


__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "conditions_match",
    "evaluate_condition",
    "field_is_enabled",
    "field_is_visible",
    "validate_field",
    "validate_form",
]
