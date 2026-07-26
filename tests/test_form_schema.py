from __future__ import annotations

import pytest

from quantas_gui.forms.catalog import ui_kit_form
from quantas_gui.forms.schema import (
    Choice,
    ChoiceField,
    FieldKind,
    FormSchema,
    FormSection,
    MatrixField,
    NumericBounds,
    TextField,
)


def test_ui_kit_schema_has_unique_fields_and_all_core_kinds() -> None:
    schema = ui_kit_form()
    keys = [field.key for field in schema.fields]
    assert len(keys) == len(set(keys))
    kinds = {field.kind for field in schema.fields}
    assert {
        FieldKind.TEXT,
        FieldKind.TEXTAREA,
        FieldKind.INTEGER,
        FieldKind.FLOAT,
        FieldKind.BOOLEAN,
        FieldKind.SELECT,
        FieldKind.MULTI_SELECT,
        FieldKind.RADIO,
        FieldKind.CHECKLIST,
        FieldKind.SLIDER,
        FieldKind.RANGE_SLIDER,
        FieldKind.RANGE_TRIPLET,
        FieldKind.VECTOR,
        FieldKind.MATRIX,
        FieldKind.FILE_UPLOAD,
        FieldKind.TAGS,
        FieldKind.KEY_VALUE,
    } <= kinds


def test_matrix_schema_rejects_non_square_symmetric_shape() -> None:
    with pytest.raises(ValueError, match="square"):
        MatrixField(key="matrix", label="Matrix", rows=2, columns=3, symmetric=True)


def test_form_rejects_duplicate_field_keys_across_sections() -> None:
    with pytest.raises(ValueError, match="field keys"):
        FormSchema(
            key="duplicate",
            title="Duplicate",
            sections=(
                FormSection("a", "A", (TextField(key="same", label="First"),)),
                FormSection("b", "B", (TextField(key="same", label="Second"),)),
            ),
        )


def test_choice_values_must_be_unique() -> None:
    with pytest.raises(ValueError, match="unique"):
        ChoiceField(
            key="choice",
            label="Choice",
            choices=(Choice("same", "A"), Choice("same", "B")),
        )


def test_numeric_bounds_require_positive_step() -> None:
    with pytest.raises(ValueError, match="positive"):
        NumericBounds(step=0)
