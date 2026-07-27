"""Frontend-neutral schemas for reusable Quantas GUI forms.

The classes in this module describe user-interface intent without importing
Dash.  A form schema can therefore be inspected, validated, tested, and reused
by a future alternative frontend before it is rendered into concrete widgets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, TypeAlias


class FieldKind(str, Enum):
    """Stable kinds understood by the Dash form renderer."""

    TEXT = "text"
    TEXTAREA = "textarea"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTI_SELECT = "multi-select"
    RADIO = "radio"
    CHECKLIST = "checklist"
    SLIDER = "slider"
    RANGE_SLIDER = "range-slider"
    RANGE_TRIPLET = "range-triplet"
    VECTOR = "vector"
    MATRIX = "matrix"
    FILE_UPLOAD = "file-upload"
    TAGS = "tags"
    KEY_VALUE = "key-value"


class ConditionOperator(str, Enum):
    """Operators available to field visibility and enablement rules."""

    EQUALS = "equals"
    NOT_EQUALS = "not-equals"
    IN = "in"
    NOT_IN = "not-in"
    TRUTHY = "truthy"
    FALSY = "falsy"
    IS_NONE = "is-none"
    IS_NOT_NONE = "is-not-none"


class FormRuleKind(str, Enum):
    """Cross-field validation rules supported by the generic validator."""

    EXACTLY_ONE = "exactly-one"
    AT_LEAST_ONE = "at-least-one"
    MUTUALLY_EXCLUSIVE = "mutually-exclusive"
    REQUIRES = "requires"


FieldWidth: TypeAlias = Literal["quarter", "third", "half", "two-thirds", "full"]
PersistenceType: TypeAlias = Literal["memory", "session", "local"]
BooleanPresentation: TypeAlias = Literal["switch", "checkbox"]
SectionPresentation: TypeAlias = Literal["panel", "details"]


@dataclass(frozen=True, slots=True)
class Choice:
    """One selectable value and its user-facing presentation.

    Parameters
    ----------
    value
        Value returned by the rendered control.
    label
        User-facing option label.
    description
        Optional concise explanation displayed by rich selectors.
    disabled
        Whether the option is visible but unavailable.
    """

    value: str | int | float | bool
    label: str
    description: str | None = None
    disabled: bool = False


@dataclass(frozen=True, slots=True)
class Condition:
    """Declarative dependency on the value of another form field."""

    field: str
    operator: ConditionOperator = ConditionOperator.EQUALS
    value: Any = None


@dataclass(frozen=True, slots=True)
class NumericBounds:
    """Bounds and stepping information for a numeric field."""

    minimum: float | int | None = None
    maximum: float | int | None = None
    step: float | int | None = None
    minimum_open: bool = False
    maximum_open: bool = False
    precision: int | None = None

    def __post_init__(self) -> None:
        """Validate internally consistent numeric bounds."""
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum")
        if self.step is not None and self.step <= 0:
            raise ValueError("numeric step must be positive")
        if self.precision is not None and self.precision < 0:
            raise ValueError("precision cannot be negative")


@dataclass(frozen=True, slots=True)
class BaseField:
    """Common metadata shared by all form fields.

    Parameters
    ----------
    key
        Stable machine-readable key. It must match the eventual API option or
        an explicit adapter key, never a translated label.
    label
        User-facing label.
    kind
        Renderer field family.
    default
        Initial raw value.
    description
        Concise help text shown below the control.
    required
        Whether an empty value is rejected before API invocation.
    disabled
        Initial disabled state.
    advanced
        Whether the field belongs to an advanced section or should receive an
        advanced visual marker.
    unit
        Optional unit displayed next to the control. It is presentation
        metadata and does not convert the submitted value.
    placeholder
        Optional empty-control hint.
    width
        Responsive width within a form grid.
    visible_when, enabled_when
        Declarative dependencies evaluated by the form state layer.
    persistence
        Whether Dash may persist the value for this field.
    persistence_type
        Browser persistence scope.
    """

    key: str
    label: str
    kind: FieldKind
    default: Any = None
    description: str | None = None
    required: bool = False
    disabled: bool = False
    advanced: bool = False
    unit: str | None = None
    placeholder: str | None = None
    width: FieldWidth = "half"
    visible_when: tuple[Condition, ...] = ()
    enabled_when: tuple[Condition, ...] = ()
    persistence: bool = False
    persistence_type: PersistenceType = "memory"

    def __post_init__(self) -> None:
        """Validate the stable field key and persistence settings."""
        if not self.key or any(char.isspace() for char in self.key):
            raise ValueError("field key must be non-empty and contain no whitespace")
        if self.persistence_type not in {"memory", "session", "local"}:
            raise ValueError("invalid persistence type")


@dataclass(frozen=True, slots=True)
class TextField(BaseField):
    """Single- or multi-line textual input."""

    kind: FieldKind = FieldKind.TEXT
    multiline: bool = False
    rows: int = 4
    max_length: int | None = None
    debounce: bool = True

    def __post_init__(self) -> None:
        """Validate textual input dimensions."""
        BaseField.__post_init__(self)
        if self.rows < 1:
            raise ValueError("textarea rows must be positive")
        if self.max_length is not None and self.max_length < 1:
            raise ValueError("max_length must be positive")


@dataclass(frozen=True, slots=True)
class NumericField(BaseField):
    """Integer or floating-point input with optional constraints."""

    kind: FieldKind = FieldKind.FLOAT
    bounds: NumericBounds = field(default_factory=NumericBounds)
    scientific: bool = False
    debounce: bool = True

    def __post_init__(self) -> None:
        """Validate the numeric field kind."""
        BaseField.__post_init__(self)
        if self.kind not in {FieldKind.INTEGER, FieldKind.FLOAT}:
            raise ValueError("NumericField kind must be integer or float")


@dataclass(frozen=True, slots=True)
class BooleanField(BaseField):
    """Boolean option rendered as a switch or a conventional checkbox."""

    kind: FieldKind = FieldKind.BOOLEAN
    presentation: BooleanPresentation = "switch"
    true_label: str = "Enabled"
    false_label: str = "Disabled"

    def __post_init__(self) -> None:
        """Validate boolean presentation."""
        BaseField.__post_init__(self)
        if self.presentation not in {"switch", "checkbox"}:
            raise ValueError("invalid boolean presentation")


@dataclass(frozen=True, slots=True)
class ChoiceField(BaseField):
    """Single- or multiple-choice field."""

    kind: FieldKind = FieldKind.SELECT
    choices: tuple[Choice, ...] = ()
    clearable: bool = False
    searchable: bool = True
    inline: bool = False

    def __post_init__(self) -> None:
        """Validate choices and selection field kind."""
        BaseField.__post_init__(self)
        if self.kind not in {
            FieldKind.SELECT,
            FieldKind.MULTI_SELECT,
            FieldKind.RADIO,
            FieldKind.CHECKLIST,
        }:
            raise ValueError("invalid choice field kind")
        values = [item.value for item in self.choices]
        if len(values) != len(set(values)):
            raise ValueError("choice values must be unique")


@dataclass(frozen=True, slots=True)
class SliderField(BaseField):
    """Bounded scalar or two-ended range slider.

    Sliders are intended for presentation controls and bounded exploratory
    inputs. Precise tolerances and scientific state coordinates should use
    :class:`NumericField` or :class:`RangeTripletField` instead.
    """

    kind: FieldKind = FieldKind.SLIDER
    bounds: NumericBounds = field(default_factory=NumericBounds)
    marks: tuple[tuple[float, str], ...] = ()
    tooltip: bool = True

    def __post_init__(self) -> None:
        """Validate slider requirements."""
        BaseField.__post_init__(self)
        if self.kind not in {FieldKind.SLIDER, FieldKind.RANGE_SLIDER}:
            raise ValueError("invalid slider field kind")
        if self.bounds.minimum is None or self.bounds.maximum is None:
            raise ValueError("sliders require finite minimum and maximum values")


@dataclass(frozen=True, slots=True)
class RangeTripletField(BaseField):
    """Exact ``start``, ``stop``, ``step`` scientific range control."""

    kind: FieldKind = FieldKind.RANGE_TRIPLET
    default: tuple[float, float, float] | None = None
    bounds: NumericBounds = field(default_factory=NumericBounds)
    labels: tuple[str, str, str] = ("Start", "Stop", "Step")
    scientific: bool = False

    def __post_init__(self) -> None:
        """Validate default triplet and labels."""
        BaseField.__post_init__(self)
        if self.default is not None and len(self.default) != 3:
            raise ValueError("range triplet default must contain three values")
        if len(self.labels) != 3:
            raise ValueError("range triplet requires three labels")


@dataclass(frozen=True, slots=True)
class VectorField(BaseField):
    """Fixed-length numeric vector editor."""

    kind: FieldKind = FieldKind.VECTOR
    length: int = 3
    labels: tuple[str, ...] = ()
    bounds: NumericBounds = field(default_factory=NumericBounds)
    scientific: bool = False

    def __post_init__(self) -> None:
        """Validate vector dimensions."""
        BaseField.__post_init__(self)
        if self.length < 1:
            raise ValueError("vector length must be positive")
        if self.labels and len(self.labels) != self.length:
            raise ValueError("vector labels must match vector length")
        if self.default is not None and len(self.default) != self.length:
            raise ValueError("vector default must match vector length")


@dataclass(frozen=True, slots=True)
class MatrixField(BaseField):
    """Editable numeric matrix backed by Dash AG Grid."""

    kind: FieldKind = FieldKind.MATRIX
    rows: int = 6
    columns: int = 6
    row_labels: tuple[str, ...] = ()
    column_labels: tuple[str, ...] = ()
    bounds: NumericBounds = field(default_factory=NumericBounds)
    symmetric: bool = False
    symmetry_tolerance: float = 1.0e-8
    allow_paste: bool = True

    def __post_init__(self) -> None:
        """Validate matrix shape and optional labels."""
        BaseField.__post_init__(self)
        if self.rows < 1 or self.columns < 1:
            raise ValueError("matrix dimensions must be positive")
        if self.row_labels and len(self.row_labels) != self.rows:
            raise ValueError("row labels must match matrix row count")
        if self.column_labels and len(self.column_labels) != self.columns:
            raise ValueError("column labels must match matrix column count")
        if self.symmetric and self.rows != self.columns:
            raise ValueError("a symmetric matrix must be square")
        if self.symmetry_tolerance < 0:
            raise ValueError("symmetry tolerance cannot be negative")


@dataclass(frozen=True, slots=True)
class FileUploadField(BaseField):
    """Browser upload field for one or more controlled input files."""

    kind: FieldKind = FieldKind.FILE_UPLOAD
    accept: tuple[str, ...] = ()
    multiple: bool = False
    max_size_bytes: int | None = None

    def __post_init__(self) -> None:
        """Validate upload size limits."""
        BaseField.__post_init__(self)
        if self.max_size_bytes is not None and self.max_size_bytes < 1:
            raise ValueError("max_size_bytes must be positive")


@dataclass(frozen=True, slots=True)
class TagsField(BaseField):
    """Repeatable scalar values entered as removable tags."""

    kind: FieldKind = FieldKind.TAGS
    value_type: Literal["text", "integer", "float"] = "text"
    choices: tuple[Choice, ...] = ()
    allow_custom: bool = True

    def __post_init__(self) -> None:
        """Validate tag value type."""
        BaseField.__post_init__(self)
        if self.value_type not in {"text", "integer", "float"}:
            raise ValueError("invalid tag value type")


@dataclass(frozen=True, slots=True)
class KeyValueField(BaseField):
    """Editable key/value records for constraints and repeated parameters."""

    kind: FieldKind = FieldKind.KEY_VALUE
    key_label: str = "Parameter"
    value_label: str = "Value"
    value_type: Literal["text", "integer", "float"] = "text"
    allow_duplicate_keys: bool = False

    def __post_init__(self) -> None:
        """Validate key/value value type."""
        BaseField.__post_init__(self)
        if self.value_type not in {"text", "integer", "float"}:
            raise ValueError("invalid key/value type")


FieldSpec: TypeAlias = (
    TextField
    | NumericField
    | BooleanField
    | ChoiceField
    | SliderField
    | RangeTripletField
    | VectorField
    | MatrixField
    | FileUploadField
    | TagsField
    | KeyValueField
)


@dataclass(frozen=True, slots=True)
class FormSection:
    """Logical and visual group of related fields."""

    key: str
    title: str
    fields: tuple[FieldSpec, ...]
    description: str | None = None
    presentation: SectionPresentation = "panel"
    collapsed: bool = False
    advanced: bool = False

    def __post_init__(self) -> None:
        """Validate field-key uniqueness within the section."""
        keys = [item.key for item in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate field key in section {self.key!r}")
        if self.presentation not in {"panel", "details"}:
            raise ValueError("invalid section presentation")


@dataclass(frozen=True, slots=True)
class FormRule:
    """Cross-field validation rule."""

    kind: FormRuleKind
    fields: tuple[str, ...]
    message: str
    when: tuple[Condition, ...] = ()

    def __post_init__(self) -> None:
        """Validate the number of fields required by the rule."""
        if len(self.fields) < 2:
            raise ValueError("cross-field rules require at least two fields")


@dataclass(frozen=True, slots=True)
class FormSchema:
    """Complete declarative form definition."""

    key: str
    title: str
    sections: tuple[FormSection, ...]
    description: str | None = None
    rules: tuple[FormRule, ...] = ()
    submit_label: str = "Run"
    reset_label: str = "Reset"

    def __post_init__(self) -> None:
        """Validate uniqueness of section and field keys."""
        section_keys = [section.key for section in self.sections]
        if len(section_keys) != len(set(section_keys)):
            raise ValueError("form section keys must be unique")
        field_keys = [field.key for section in self.sections for field in section.fields]
        if len(field_keys) != len(set(field_keys)):
            raise ValueError("form field keys must be unique")
        known = set(field_keys)
        for rule in self.rules:
            missing = set(rule.fields) - known
            if missing:
                raise ValueError(f"form rule references unknown fields: {sorted(missing)}")

    @property
    def fields(self) -> tuple[FieldSpec, ...]:
        """Return all fields in deterministic section order."""
        return tuple(field for section in self.sections for field in section.fields)

    def field(self, key: str) -> FieldSpec:
        """Return one field by stable key.

        Raises
        ------
        KeyError
            If the form has no field with the requested key.
        """
        for item in self.fields:
            if item.key == key:
                return item
        raise KeyError(key)


__all__ = [
    "BaseField",
    "BooleanField",
    "Choice",
    "ChoiceField",
    "Condition",
    "ConditionOperator",
    "FieldKind",
    "FieldSpec",
    "FileUploadField",
    "FormRule",
    "FormRuleKind",
    "FormSchema",
    "FormSection",
    "KeyValueField",
    "MatrixField",
    "NumericBounds",
    "NumericField",
    "RangeTripletField",
    "SliderField",
    "TagsField",
    "TextField",
    "VectorField",
]
