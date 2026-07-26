from __future__ import annotations

from quantas_gui.forms.catalog import ui_kit_form
from quantas_gui.forms.schema import (
    FieldKind,
    FormRule,
    FormRuleKind,
    FormSchema,
    FormSection,
    MatrixField,
    NumericBounds,
    NumericField,
    RangeTripletField,
)
from quantas_gui.forms.validation import validate_field, validate_form


def test_integer_validation_does_not_silently_truncate() -> None:
    field = NumericField(key="count", label="Count", kind=FieldKind.INTEGER)
    value, issues = validate_field(field, 2.5)
    assert value == 2.5
    assert issues[0].code == "invalid-value"


def test_scientific_number_accepts_exponent_string() -> None:
    field = NumericField(
        key="rtol",
        label="Tolerance",
        scientific=True,
        bounds=NumericBounds(minimum=0.0),
    )
    value, issues = validate_field(field, "1e-10")
    assert value == 1.0e-10
    assert issues == ()


def test_range_triplet_checks_step_direction() -> None:
    field = RangeTripletField(key="temperature", label="Temperature")
    _, issues = validate_field(field, (300.0, 1000.0, -50.0))
    assert any(issue.code == "step-direction" for issue in issues)


def test_symmetric_matrix_is_checked() -> None:
    field = MatrixField(
        key="stiffness",
        label="Stiffness",
        rows=2,
        columns=2,
        symmetric=True,
    )
    _, issues = validate_field(field, ((1.0, 2.0), (3.0, 4.0)))
    assert any(issue.code == "matrix-symmetry" for issue in issues)


def test_exactly_one_cross_field_rule() -> None:
    schema = FormSchema(
        key="compare",
        title="Compare",
        sections=(
            FormSection(
                "coordinates",
                "Coordinates",
                (
                    NumericField(key="pressure", label="Pressure"),
                    NumericField(key="temperature", label="Temperature"),
                ),
            ),
        ),
        rules=(
            FormRule(
                FormRuleKind.EXACTLY_ONE,
                ("pressure", "temperature"),
                "Set exactly one coordinate.",
            ),
        ),
    )
    assert validate_form(schema, {"pressure": 1.0}).valid
    assert not validate_form(schema, {}).valid
    assert not validate_form(schema, {"pressure": 1.0, "temperature": 300.0}).valid


def test_ui_kit_defaults_require_one_fixed_coordinate() -> None:
    schema = ui_kit_form()
    result = validate_form(schema, {field.key: field.default for field in schema.fields})
    assert not result.valid
    assert any(issue.code == "exactly-one" for issue in result.issues)
